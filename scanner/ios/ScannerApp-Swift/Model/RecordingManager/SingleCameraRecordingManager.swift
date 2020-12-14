//
//  SingleCameraRecordingManager.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-11-18.
//  Copyright © 2020 jx16. All rights reserved.
//

import AVFoundation
import CoreLocation

class SingleCameraRecordingManager: NSObject {
    
    private let sessionQueue = DispatchQueue(label: "single camera recording queue")
    
    private let session = AVCaptureSession()

    private let motionManager = MotionManager()
    
    private var dirUrl: URL!
    private var recordingId: String!
    private var movieFilePath: String!

    private let movieFileOutput = AVCaptureMovieFileOutput()
    
    private let locationManager = CLLocationManager()
    private var gpsLocation: [Double] = []
    
    private var colorResolution: [Int] = []
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
        
        guard let videoDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
            print("Wide angle camera is unavailable.")
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
        
        if session.canAddOutput(movieFileOutput) {
            session.addOutput(movieFileOutput)

            if let connection = movieFileOutput.connection(with: .video) {
                if connection.isVideoStabilizationSupported {
                    connection.preferredVideoStabilizationMode = .auto
                }
                
                connection.videoOrientation = .landscapeRight
                
                let availableVideoCodecTypes = movieFileOutput.availableVideoCodecTypes
                
                if availableVideoCodecTypes.contains(.h264) {
                    movieFileOutput.setOutputSettings([AVVideoCodecKey: AVVideoCodecType.h264], for: connection)
                }
            }
        }
        
        session.commitConfiguration()

        // set video resulotion to 1920x1440 and framerate to 60 fps if possible
        for format in videoDevice.formats {

            let videoFormatDescription = format.formatDescription
            let dimensions = CMVideoFormatDescriptionGetDimensions(videoFormatDescription)

            let framerate = format.videoSupportedFrameRateRanges[0]

            if framerate.maxFrameRate >= 60 && dimensions.width >= 1920 && dimensions.height >= 1440 {

                do {
                    try videoDevice.lockForConfiguration()
                    
                    videoDevice.activeFormat = format
                                    
                    let targetFrameDuration = CMTimeMake(value: 1, timescale: Int32(60))
                    videoDevice.activeVideoMaxFrameDuration = targetFrameDuration
                    videoDevice.activeVideoMinFrameDuration = targetFrameDuration
                    
                    videoDevice.unlockForConfiguration()
                } catch {
                    print("Error configurating video device")
                }

                break
            }
            
        }

        let videoFormatDescription = videoDevice.activeFormat.formatDescription
        let dimensions = CMVideoFormatDescriptionGetDimensions(videoFormatDescription)
        
        let width = Int(dimensions.width)
        let height = Int(dimensions.height)
        colorResolution = [height, width]
        
        let fov = videoDevice.activeFormat.videoFieldOfView
//        let aspect = Float(width) / Float(height)
        let t = tan((0.5 * fov) * Float.pi / 180)
        
        let fx = 0.5 * Float(width) / t
//        let fy = 0.5 * Float(height) / t
        let fy = fx
        
        let mx = Float(width - 1) / 2.0
        let my = Float(height - 1) / 2.0
        
        cameraIntrinsicArray = [fx, 0.0, 0.0, 0.0, fy, 0.0, mx, my, 1.0]
        
    }

}

extension SingleCameraRecordingManager: RecordingManager {
    
    var isRecording: Bool {
        return movieFileOutput.isRecording
    }
    
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
            
            // TODO:
            // Camera data
            
            // Motion data
            motionManager.startRecording(dataPathString: dirUrl.path, recordingId: recordingId)
            
            // Video
            movieFilePath = (dirUrl.path as NSString).appendingPathComponent((recordingId as NSString).appendingPathExtension("mp4")!)
            movieFileOutput.startRecording(to: URL(fileURLWithPath: movieFilePath), recordingDelegate: self)
    
        }
        
    }
    
    func stopRecording() {
        
        sessionQueue.async {
            self.movieFileOutput.stopRecording()
        }
        
    }
    
}

extension SingleCameraRecordingManager: AVCaptureFileOutputRecordingDelegate {
    
    func fileOutput(_ output: AVCaptureFileOutput,
                    didFinishRecordingTo outputFileURL: URL,
                    from connections: [AVCaptureConnection],
                    error: Error?) {
        
        if error != nil {
            print("Movie file finishing error: \(String(describing: error))")
        }
        
        sessionQueue.async { [self] in
            
            var streamInfo: [StreamInfo] = motionManager.stopRecordingAndReturnStreamInfo()

            let numColorFrames = VideoHelper.getNumberOfFrames(videoUrl: outputFileURL)
            
            let cameraStreamInfo = CameraStreamInfo(id: "color_back_1", type: "color_camera", encoding: "h264", frequency: 60, numberOfFrames: numColorFrames, fileExtension: "mp4", resolution: colorResolution, intrinsics: cameraIntrinsicArray, extrinsics: nil)
            
            streamInfo.append(cameraStreamInfo)
            
            let metadata = Metadata(username: username ?? "", userInputDescription: sceneDescription ?? "", sceneType: sceneType ?? "", gpsLocation: gpsLocation, streams: streamInfo, numberOfFiles: 7)
            
            let metadataPath = (dirUrl.path as NSString).appendingPathComponent((recordingId as NSString).appendingPathExtension("json")!)
            
            metadata.display()
            metadata.writeToFile(filepath: metadataPath)
            
            username = nil
            sceneDescription = nil
            sceneType = nil
            
        }
        
    }
    
}
