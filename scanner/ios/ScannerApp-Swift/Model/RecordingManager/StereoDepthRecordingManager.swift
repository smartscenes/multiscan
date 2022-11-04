//
//  TestSynchronizerRecordingManager.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2021-01-28.
//  Copyright © 2021 jx16. All rights reserved.
//

import AVFoundation
import CoreLocation

@available(iOS 13.0, *)
class StereoDepthRecordingManager: NSObject {
    
    private let sessionQueue = DispatchQueue(label: "single camera recording queue")
    
    private let session = AVCaptureSession()

    private let motionManager = MotionManager()
    
    private let depthRecorder = DepthRecorder()
    private var rgbRecorder: RGBRecorder! = nil
    
    private var dirUrl: URL!
    private var recordingId: String!
    private var numColorFrames: Int = 0
    private var numDepthFrames: Int = 0
    
    // this variable is to help track if depth frames are available at expected rate.
    private var depthFrameNotAvailableFlag: Bool = false

    var isRecording: Bool = false
    
    private let videoDataOutput = AVCaptureVideoDataOutput()
    private let depthDataOutput = AVCaptureDepthDataOutput()
    
    private var outputSynchronizer: AVCaptureDataOutputSynchronizer?
    
    private let locationManager = CLLocationManager()
    private var gpsLocation: [Double] = []
    
    private var colorResolution: [Int] = []
    private var depthRecolution: [Int] = []
    
    private var colorFrequency: Int?
    private var depthFrequency: Int?
    
    private var cameraIntrinsicArray: [Float]?
    
    private var username: String?
    private var sceneDescription: String?
    private var sceneType: String?
    
    override init() {
        super.init()

        locationManager.requestWhenInUseAuthorization()
        
        sessionQueue.async {
            
            self.configureSession()
            
            self.session.startRunning()
        }
    }
    
    deinit {
        sessionQueue.sync {
            self.session.stopRunning()
        }
    }
    
    private func configureSession() {
        
        var videoDevice: AVCaptureDevice
        
        if let dualWideCameraDevice = AVCaptureDevice.default(.builtInDualWideCamera, for: .video, position: .back) {
            videoDevice = dualWideCameraDevice
            print("Selected builtInDualWideCamera")
            
        } else if let dualCameraDevice = AVCaptureDevice.default(.builtInDualCamera, for: .video, position: .back) {
            videoDevice = dualCameraDevice
            print("Selected builtInDualCamera")
            
        } else {
            print("No dual camera device (builtInDualWideCamera, builtInDualCamera) is available.")
            return
        }

        session.beginConfiguration()
        
        session.sessionPreset = .inputPriority
        
        do {

            let videoDeviceInput = try AVCaptureDeviceInput(device: videoDevice)

            if session.canAddInput(videoDeviceInput) {
                session.addInput(videoDeviceInput)
            } else {
                print("Couldn't add video device input to the session.")
                session.commitConfiguration()
                return
            }
            
        } catch {
            print("Couldn't create video device input: \(error)")
            session.commitConfiguration()
            return
        }
        
        if session.canAddOutput(videoDataOutput) {
            session.addOutput(videoDataOutput)
            
            if let connection = videoDataOutput.connection(with: .video) {
                
                connection.videoOrientation = .landscapeRight
                
//                if connection.isCameraIntrinsicMatrixDeliverySupported {
//                    connection.isCameraIntrinsicMatrixDeliveryEnabled = true
//                } else {
//                    print("Camera intrinsic matrix delivery not supported.")
//                }
                
                videoDataOutput.alwaysDiscardsLateVideoFrames = false
                
            }
        }
        
        if session.canAddOutput(depthDataOutput) {
            session.addOutput(depthDataOutput)
            
            if let connection = depthDataOutput.connection(with: .depthData) {
                print(connection.isEnabled)
                connection.videoOrientation = .landscapeRight
                
                // TODO: do more test on this
                depthDataOutput.isFilteringEnabled = true
                
                depthDataOutput.alwaysDiscardsLateDepthData = false
            }
        } else {
            print("Unable to add depth data output.")
        }
        
        outputSynchronizer = AVCaptureDataOutputSynchronizer(dataOutputs: [videoDataOutput, depthDataOutput])
        outputSynchronizer!.setDelegate(self, queue: sessionQueue)

        session.commitConfiguration()

        for format in videoDevice.formats.reversed() {

            let framerate = format.videoSupportedFrameRateRanges[0]

            let videoFormatDescription = format.formatDescription
            let dimensions = CMVideoFormatDescriptionGetDimensions(videoFormatDescription)
            print("width: \(dimensions.width), height: \(dimensions.height), fps: \(framerate.maxFrameRate)")

            let depthFormats = format.supportedDepthDataFormats
            let depthFloat16Formats = depthFormats.filter({
                CMFormatDescriptionGetMediaSubType($0.formatDescription) == kCVPixelFormatType_DepthFloat16
            })

            if framerate.maxFrameRate >= 60 && !depthFloat16Formats.isEmpty {

                do {
                    try videoDevice.lockForConfiguration()

                    videoDevice.activeFormat = format

                    let targetFrameDuration = CMTimeMake(value: 1, timescale: Int32(60))
                    videoDevice.activeVideoMaxFrameDuration = targetFrameDuration
                    videoDevice.activeVideoMinFrameDuration = targetFrameDuration
                    videoDevice.videoZoomFactor = format.videoMinZoomFactorForDepthDataDelivery

                    let depthFormat = depthFloat16Formats.max(by: {
                        first, second in CMVideoFormatDescriptionGetDimensions(first.formatDescription).width < CMVideoFormatDescriptionGetDimensions(second.formatDescription).width
                    })

                    videoDevice.activeDepthDataFormat = depthFormat

                    videoDevice.unlockForConfiguration()
                } catch {
                    print("Error configurating video device")
                }

                break
            }

        }

        let videoFormat = videoDevice.activeFormat
        let dimensions = CMVideoFormatDescriptionGetDimensions(videoFormat.formatDescription)
        
        let height = Int(dimensions.height)
        let width = Int(dimensions.width)
        colorResolution = [height, width]
        colorFrequency = Int(videoFormat.videoSupportedFrameRateRanges[0].maxFrameRate)
        
        let fov = videoFormat.videoFieldOfView
//        let aspect = Float(width) / Float(height)
        let t = tan((0.5 * fov) * Float.pi / 180)
        
        let fx = 0.5 * Float(width) / t
//        let fy = 0.5 * Float(height) / t
        let fy = fx
        
        let mx = Float(width - 1) / 2.0
        let my = Float(height - 1) / 2.0
        
        cameraIntrinsicArray = [fx, 0.0, 0.0, 0.0, fy, 0.0, mx, my, 1.0]
        
        let videoSettings: [String: Any] = [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoHeightKey: NSNumber(value: colorResolution[0]), AVVideoWidthKey: NSNumber(value: colorResolution[1])]
        rgbRecorder = RGBRecorder(videoSettings: videoSettings)
        
        let depthFormat = videoDevice.activeDepthDataFormat!
        let depthDimensions = CMVideoFormatDescriptionGetDimensions(depthFormat.formatDescription)
        depthRecolution = [Int(depthDimensions.height), Int(depthDimensions.width)]
        depthFrequency = Int(depthFormat.videoSupportedFrameRateRanges[0].maxFrameRate)
        
        print(videoFormat)
        print(depthFormat)
        
    }

}

@available(iOS 13.0, *)
extension StereoDepthRecordingManager: RecordingManager {
    
    func getSession() -> NSObject {
        return session
    }
    
    func startRecording(username: String, sceneDescription: String, sceneType: String) {
        
        sessionQueue.async { [self] in
            
            self.username = username
            self.sceneDescription = sceneDescription
            self.sceneType = sceneType
            
            gpsLocation = Helper.getGpsLocation(locationManager: locationManager)
            
            recordingId = Helper.getRecordingId()
            dirUrl = URL(fileURLWithPath: Helper.getRecordingDataDirectoryPath(recordingId: recordingId))

            // Motion data
            motionManager.startRecording(dataPathString: dirUrl.path, recordingId: recordingId)
            
            rgbRecorder.prepareForRecording(dirPath: dirUrl.path, filename: recordingId)
            depthRecorder.prepareForRecording(dirPath: dirUrl.path, filename: recordingId)
            
            numColorFrames = 0
            numDepthFrames = 0
            
            isRecording = true
            
            print("Start recording ...")
    
        }
        
    }
    
    func stopRecording() {
        
        sessionQueue.async { [self] in

            isRecording = false
            
            rgbRecorder.finishRecording()
            depthRecorder.finishRecording()
            
            let imuStreamInfo = motionManager.stopRecordingAndReturnStreamInfo()
            
            writeMetadataToFile(imuStreamsInfo: imuStreamInfo)
            
            username = nil
            sceneDescription = nil
            sceneType = nil
        }
        
    }
    
    private func writeMetadataToFile(imuStreamsInfo: [ImuStreamInfo]) {

        let colorStreamInfo = CameraStreamInfo(id: "color_back_1", type: "color_camera", encoding: "h264", frequency: colorFrequency ?? 0, numberOfFrames: numColorFrames, fileExtension: "mp4", resolution: colorResolution, intrinsics: cameraIntrinsicArray, extrinsics: nil)
        let depthStreamInfo = CameraStreamInfo(id: "stereo_depth_1", type: "dual_camera_stereo_depth", encoding: "float16_zlib", frequency: depthFrequency ?? 0, numberOfFrames: numDepthFrames, fileExtension: "depth.zlib", resolution: depthRecolution, intrinsics: nil, extrinsics: nil)

        var streamsInfo: [StreamInfo] = [colorStreamInfo, depthStreamInfo]
        streamsInfo.append(contentsOf: imuStreamsInfo)
        
        let metadata = Metadata(username: username ?? "", userInputDescription: sceneDescription ?? "", sceneType: sceneType ?? "", gpsLocation: gpsLocation, streams: streamsInfo, numberOfFiles: 8)

        let metadataPath = (dirUrl.path as NSString).appendingPathComponent((recordingId as NSString).appendingPathExtension("json")!)

        metadata.display()
        metadata.writeToFile(filepath: metadataPath)
    }
    
}

@available(iOS 13.0, *)
extension StereoDepthRecordingManager: AVCaptureDataOutputSynchronizerDelegate {
    /// capture depth data and rgb data
    func dataOutputSynchronizer(_ synchronizer: AVCaptureDataOutputSynchronizer, didOutput synchronizedDataCollection: AVCaptureSynchronizedDataCollection) {
        
//        print("================")
//        print("@AVCaptureDataOutputSynchronizerDelegate: got data collection")
        
        // notes:
        // if video frame not available -> red flag
        // if depth frame not availabel -> okay
        // if depth frame not availabel twice in a row -> red flag
        
        if !isRecording {
            return
        }
        
        if let syncedDepthData: AVCaptureSynchronizedDepthData =
            synchronizedDataCollection.synchronizedData(for: depthDataOutput) as? AVCaptureSynchronizedDepthData {
            
            depthFrameNotAvailableFlag = false
            
            if syncedDepthData.depthDataWasDropped {
                print("@AVCaptureDataOutputSynchronizerDelegate: depth data was dropped. Dropped reason: \(syncedDepthData.droppedReason.rawValue)")
                
                // TODO: how to get drop reason description
                print(syncedDepthData.droppedReason.rawValue)
                
            } else {
//                print("@AVCaptureDataOutputSynchronizerDelegate: got depth data")
                
                depthRecorder.updateWithoutConversion(syncedDepthData.depthData.depthDataMap)
                numDepthFrames += 1
                
                // TODO: see if other variables like accuracy are useful
                
            }
        } else {
//            print("@AVCaptureDataOutputSynchronizerDelegate: no depth available")
            
            // Assuming color frames are available at 60 fps and depth frames are 30 fps.
            // we should recieve one depth frames every two sync data
            if depthFrameNotAvailableFlag {
                print("@AVCaptureDataOutputSynchronizerDelegate: Depth frames are missing from two or more consecutive sync data.")
            } else {
                depthFrameNotAvailableFlag = true
            }
            
        }
        
        if let syncedVideoData: AVCaptureSynchronizedSampleBufferData =
            synchronizedDataCollection.synchronizedData(for: videoDataOutput) as? AVCaptureSynchronizedSampleBufferData {
            
            if syncedVideoData.sampleBufferWasDropped {
                print("@AVCaptureDataOutputSynchronizerDelegate: sample buffer was dropped. Dropped reason: \(syncedVideoData.droppedReason.rawValue)")
                
            } else {
//                print("@AVCaptureDataOutputSynchronizerDelegate: got sample buffer")
                
                rgbRecorder.update(buffer: syncedVideoData.sampleBuffer)
                numColorFrames += 1
                
                // TODO: we can potentially record intrinsics
                
            }
        } else {
            print("@AVCaptureDataOutputSynchronizerDelegate: no sample buffer available")
        }
        
    }
    
}
