//
//  DualCameraRecordingManager.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-12-11.
//  Copyright © 2020 jx16. All rights reserved.
//

import AVFoundation
import CoreLocation

@available(iOS 13.0, *)
class DualCameraRecordingManager: NSObject {
    
    private let session = AVCaptureMultiCamSession()
    
    private let sessionQueue = DispatchQueue(label: "session queue")
    
    private let motionManager = MotionManager()
    
    private var dirUrl: URL!
    private var recordingId: String!
    private var primaryVideoFilePath: String!
    private var secondaryVideoFilePath: String!
    
    private let locationManager = CLLocationManager()
    private var gpsLocation: [Double] = []
    
    private var primaryCameraInput: AVCaptureDeviceInput?
    private let primaryCameraOutput = AVCaptureMovieFileOutput()
    
    private var secondaryCameraInput: AVCaptureDeviceInput?
    private let secondaryCameraOutput = AVCaptureMovieFileOutput()
    
    private var username: String?
    private var sceneDescription: String?
    private var sceneType: String?
    
    private var primaryVideoRecordingFinished = false
    private var secondaryVideoRecordingFinished = false
    
    private var primaryCameraResolution: [Int] = []
    private var primaryCameraIntrinsicArray: [Float] = []
    private var primaryCameraFramerate: Int = -1
    
    private var secondaryCameraResolution: [Int] = []
    private var secondaryCameraIntrinsicArray: [Float] = []
    private var secondaryCameraFramerate: Int = -1
    
    private var extrinsicsPrimaryToSecondary: [Float] = []
    private var extrinsicsSecondaryToPrimary: [Float] = []
    
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
        
        session.beginConfiguration()
        defer {
            session.commitConfiguration()
        }
        
        // Get devices
        guard let primaryCameraDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
            print("Could not find the wide angle camera")
            return
        }
        
        var secondaryCameraDevice: AVCaptureDevice
        
        if let ultrawideCameraDevice = AVCaptureDevice.default(.builtInUltraWideCamera, for: .video, position: .back) {
            secondaryCameraDevice = ultrawideCameraDevice
        } else if let telephotoCameraDevice = AVCaptureDevice.default(.builtInTelephotoCamera, for: .video, position: .back) {
            secondaryCameraDevice = telephotoCameraDevice
        } else {
            print("Could not find either ultrawide or telephone camera")
            return
        }
        
        // Add input
        do {
            primaryCameraInput = try AVCaptureDeviceInput(device: primaryCameraDevice)
            
            guard let primaryCameraInput = primaryCameraInput, session.canAddInput(primaryCameraInput) else {
                print("Could not add wide angle camera device input")
                return
            }
            
            session.addInputWithNoConnections(primaryCameraInput)
        } catch {
            print("Couldn't create wide angle camera device input: \(error)")
            return
        }
        
        do {
            secondaryCameraInput = try AVCaptureDeviceInput(device: secondaryCameraDevice)
            
            guard let secondaryCameraInput = secondaryCameraInput, session.canAddInput(secondaryCameraInput) else {
                print("Could not add secondary camera device input")
                return
            }
            
            session.addInputWithNoConnections(secondaryCameraInput)
        } catch {
            print("Couldn't create secondary camera device input: \(error)")
            return
        }

        // Add output
        guard session.canAddOutput(primaryCameraOutput) else {
            print("Could not add wide-angle camera output")
            return
        }
        session.addOutputWithNoConnections(primaryCameraOutput)
        
        guard session.canAddOutput(secondaryCameraOutput) else {
            print("Could not add secondary camera output")
            return
        }
        session.addOutputWithNoConnections(secondaryCameraOutput)
        
        // Setup input/output connection
        guard let primaryCameraPort = primaryCameraInput!.ports(for: .video,
                                                   sourceDeviceType: .builtInWideAngleCamera,
                                                   sourceDevicePosition: primaryCameraDevice.position).first
        else {
                print("Could not obtain wide angle camera input ports")
                return
        }
        
        let secondaryCameraPort: AVCaptureInput.Port
        
        if secondaryCameraDevice.deviceType == .builtInUltraWideCamera {
            secondaryCameraPort = secondaryCameraInput!.ports(for: .video,
                                                              sourceDeviceType: .builtInUltraWideCamera,
                                                              sourceDevicePosition: secondaryCameraDevice.position).first!
        } else if secondaryCameraDevice.deviceType == .builtInTelephotoCamera {
            secondaryCameraPort = secondaryCameraInput!.ports(for: .video,
                                                              sourceDeviceType: .builtInTelephotoCamera,
                                                              sourceDevicePosition: secondaryCameraDevice.position).first!
        } else {
            print("Could not obtain secondary camera input ports")
            return
        }
        
        let primaryCameraConnection = AVCaptureConnection(inputPorts: [primaryCameraPort], output: primaryCameraOutput)
        guard session.canAddConnection(primaryCameraConnection) else {
            print("Cannot add wide-angle input to output")
            return
        }
        session.addConnection(primaryCameraConnection)
        primaryCameraConnection.videoOrientation = .landscapeRight
        
        let primaryCameraAvailableVideoCodecTypes = primaryCameraOutput.availableVideoCodecTypes
        if primaryCameraAvailableVideoCodecTypes.contains(.h264) {
            primaryCameraOutput.setOutputSettings([AVVideoCodecKey: AVVideoCodecType.h264], for: primaryCameraConnection)
        }
        
        let secondaryCameraConnection = AVCaptureConnection(inputPorts: [secondaryCameraPort], output: secondaryCameraOutput)
        guard session.canAddConnection(secondaryCameraConnection) else {
            print("Cannot add secondary input to output")
            return
        }
        session.addConnection(secondaryCameraConnection)
        secondaryCameraConnection.videoOrientation = .landscapeRight
        
        let secondaryCameraAvailableVideoCodecTypes = secondaryCameraOutput.availableVideoCodecTypes
        if secondaryCameraAvailableVideoCodecTypes.contains(.h264) {
            secondaryCameraOutput.setOutputSettings([AVVideoCodecKey: AVVideoCodecType.h264], for: secondaryCameraConnection)
        }
        
        configureVideoQuality()
        
        updateCameraInfo()
        
    }
    
    /// set video quality and reduce video quality if needed
    private func configureVideoQuality() {
        
        // Set to highest first
        for format in primaryCameraInput!.device.formats.reversed() {
            if format.isMultiCamSupported {

                let dims = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
                
                let framerate = format.videoSupportedFrameRateRanges[0]
                
                if framerate.maxFrameRate < 60.0 {
                    continue
                }

                do {
                    try primaryCameraInput?.device.lockForConfiguration()
                    primaryCameraInput?.device.activeFormat = format
                    primaryCameraInput?.device.unlockForConfiguration()
                } catch {
                    print("Could not lock primary camera device for configuration: \(error)")
                }
                
                print("primary, width: \(dims.width), height: \(dims.height), framerate: \(framerate.maxFrameRate)")

                break
            }
        }

        for format in secondaryCameraInput!.device.formats.reversed() {
            if format.isMultiCamSupported {

                let dims = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
                
                let framerate = format.videoSupportedFrameRateRanges[0]

                if framerate.maxFrameRate < 60.0 {
                    continue
                }
                
                do {
                    try secondaryCameraInput?.device.lockForConfiguration()
                    secondaryCameraInput?.device.activeFormat = format
                    secondaryCameraInput?.device.unlockForConfiguration()
                } catch {
                    print("Could not lock primary camera device for configuration: \(error)")
                }

                print("secondary, width: \(dims.width), height: \(dims.height), framerate: \(framerate.maxFrameRate)")
                
                break
            }
        }
        
        // reduce video quality if needed
        while true {

            if session.hardwareCost <= 1.0 && session.systemPressureCost <= 1.0 {
                break
            }

            reduceResolution()
            
            if session.hardwareCost <= 1.0 && session.systemPressureCost <= 1.0 {
                break
            }
            
            reduceFramerate()
            
        }
        
    }

    private func reduceResolution() {

        let primaryCameraDims = CMVideoFormatDescriptionGetDimensions(primaryCameraInput!.device.activeFormat.formatDescription)
        let activeWidthPrimary = primaryCameraDims.width
        let activeHeightPrimary = primaryCameraDims.height
        
        let secondaryCameraDims = CMVideoFormatDescriptionGetDimensions(secondaryCameraInput!.device.activeFormat.formatDescription)
        let activeWidthSecondary = secondaryCameraDims.width
        let activeHeightSecondary = secondaryCameraDims.height
        
        if activeWidthPrimary > activeWidthSecondary || activeHeightPrimary > activeHeightSecondary {
            print("reducing primary resolution")
            reduceResolution(device: primaryCameraInput!.device)
            
            do {
                try secondaryCameraInput!.device.lockForConfiguration()
                secondaryCameraInput!.videoMinFrameDurationOverride = CMTimeMake(value: 1, timescale: 60)
                secondaryCameraInput!.device.unlockForConfiguration()
                print("secondary, framerate reset to 60")
            } catch {
                print("Could not lock secondary camera device for configuration: \(error)")
            }
            
        } else {
            print("reducing secondary resolution")
            reduceResolution(device: secondaryCameraInput!.device)
            
            do {
                try primaryCameraInput!.device.lockForConfiguration()
                primaryCameraInput!.videoMinFrameDurationOverride = CMTimeMake(value: 1, timescale: 60)
                primaryCameraInput!.device.unlockForConfiguration()
                print("primary, framerate reset to 60")
            } catch {
                print("Could not lock primary camera device for configuration: \(error)")
            }
        }

    }
    
    private func reduceResolution(device: AVCaptureDevice) {
        
        let activeFormat = device.activeFormat
        
        let activeDims = CMVideoFormatDescriptionGetDimensions(activeFormat.formatDescription)
        let activeWidth = activeDims.width
        let activeHeight = activeDims.height
        
        let formats = device.formats
        if let formatIndex = formats.firstIndex(of: activeFormat) {
            
            for index in (0..<formatIndex).reversed() {
                
                let format = device.formats[index]
                
                let framerate = format.videoSupportedFrameRateRanges[0]
                
                if format.isMultiCamSupported && framerate.maxFrameRate >= 60.0 {
                    
                    let dims = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
                    let width = dims.width
                    let height = dims.height
                    
                    if width < activeWidth || height < activeHeight {
                        do {
                            try device.lockForConfiguration()
                            device.activeFormat = format
                            device.unlockForConfiguration()
                            
                            print("width \(activeWidth) -> \(width), height \(activeHeight) -> \(height)")
                            
                        } catch {
                            print("Could not lock device for configuration: \(error)")
                        }
                        
                    }
                }
            }
        }
        
    }
    
    private func reduceFramerate() {
        
        print("reducing framerate")
        
        let primaryCameraMinFrameDuration = primaryCameraInput!.device.activeVideoMinFrameDuration
        let primaryCameraActiveMaxFramerate: Double = Double(primaryCameraMinFrameDuration.timescale) / Double(primaryCameraMinFrameDuration.value)
        
        let secondaryCameraMinFrameDuration = secondaryCameraInput!.device.activeVideoMinFrameDuration
        let secondaryCameraActiveMaxFramerate: Double = Double(secondaryCameraMinFrameDuration.timescale) / Double(secondaryCameraMinFrameDuration.value)
        
        var targetFramerate = primaryCameraActiveMaxFramerate
        if primaryCameraActiveMaxFramerate > 60.0 || secondaryCameraActiveMaxFramerate > 60.0 {
            targetFramerate = 60.0
        } else if primaryCameraActiveMaxFramerate > 45.0 || secondaryCameraActiveMaxFramerate > 45.0 {
            targetFramerate = 45.0
        } else if primaryCameraActiveMaxFramerate > 30.0 || secondaryCameraActiveMaxFramerate > 30.0 {
            targetFramerate = 30.0
        } else {
            return
        }
        
        do {
            try primaryCameraInput!.device.lockForConfiguration()
            primaryCameraInput!.videoMinFrameDurationOverride = CMTimeMake(value: 1, timescale: Int32(targetFramerate))
            primaryCameraInput!.device.unlockForConfiguration()
            
            print("primary, framerate \(primaryCameraActiveMaxFramerate) -> \(targetFramerate)")
            
        } catch {
            print("Could not lock primary camera device for configuration: \(error)")
        }
        
        do {
            try secondaryCameraInput!.device.lockForConfiguration()
            secondaryCameraInput!.videoMinFrameDurationOverride = CMTimeMake(value: 1, timescale: Int32(targetFramerate))
            secondaryCameraInput!.device.unlockForConfiguration()
            
            print("secondary, framerate \(secondaryCameraActiveMaxFramerate) -> \(targetFramerate)")
            
        } catch {
            print("Could not lock secondary camera device for configuration: \(error)")
        }
        
    }
    
    private func updateCameraInfo() {
        
        updatePrimaryCameraInfo()
        updateSecondaryCameraInfo()
        
        updateExtrinsics()
        
    }
    
    private func updatePrimaryCameraInfo() {
        
        let format = primaryCameraInput!.device.activeFormat
        let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
        
        let width = Int(dimensions.width)
        let height = Int(dimensions.height)
        primaryCameraResolution = [height, width]
        primaryCameraIntrinsicArray = calculateIntrinsics(width: Float(width), height: Float(height), fov: format.videoFieldOfView)
        
        let minFrameDuration = primaryCameraInput!.device.activeVideoMinFrameDuration
        primaryCameraFramerate = Int(Double(minFrameDuration.timescale) / Double(minFrameDuration.value))
        
    }
    
    private func updateSecondaryCameraInfo() {
        
        let format = secondaryCameraInput!.device.activeFormat
        let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
        
        let width = Int(dimensions.width)
        let height = Int(dimensions.height)
        secondaryCameraResolution = [height, width]
        secondaryCameraIntrinsicArray = calculateIntrinsics(width: Float(width), height: Float(height), fov: format.videoFieldOfView)
        
        let minFrameDuration = secondaryCameraInput!.device.activeVideoMinFrameDuration
        secondaryCameraFramerate = Int(Double(minFrameDuration.timescale) / Double(minFrameDuration.value))
        
    }
    
    private func calculateIntrinsics(width: Float, height: Float, fov: Float) -> [Float] {

        let t = tan((0.5 * fov) * Float.pi / 180)
        let fx = 0.5 * width / t
        let fy = fx
        
        let mx = (width - 1.0) / 2.0
        let my = (height - 1.0) / 2.0
        
        return [fx, 0.0, 0.0, 0.0, fy, 0.0, mx, my, 1.0]
        
    }
    
    private func updateExtrinsics() {
        
        extrinsicsPrimaryToSecondary = getExtrinsics(from: primaryCameraInput!.device, to: secondaryCameraInput!.device)
        extrinsicsSecondaryToPrimary = getExtrinsics(from: secondaryCameraInput!.device, to: primaryCameraInput!.device)
        
    }
    
    private func getExtrinsics(from fromDevice: AVCaptureDevice, to toDevice: AVCaptureDevice) -> [Float] {
        
        let extrinsics = AVCaptureDevice.extrinsicMatrix(from: fromDevice, to: toDevice)
        
        let extrinsicsPointer = UnsafeMutableBufferPointer<simd_float4x3>.allocate(capacity: MemoryLayout<simd_float4x3>.size)
        _ = extrinsics?.copyBytes(to: extrinsicsPointer)
        
        let extrinsicsArray = extrinsicsPointer.first?.arrayRepresentation ?? []
        
        return extrinsicsArray
        
    }
    
}

@available(iOS 13.0, *)
extension DualCameraRecordingManager: RecordingManager {
    
    var isRecording: Bool {
        
        if primaryCameraOutput.isRecording && secondaryCameraOutput.isRecording {
            return true
        } else if !primaryCameraOutput.isRecording && !secondaryCameraOutput.isRecording {
            return false
        } else {
            print("MultiCam session is at unexpected state")
            
            if primaryCameraOutput.isRecording {
                primaryCameraOutput.stopRecording()
            }
            if secondaryCameraOutput.isRecording {
                secondaryCameraOutput.stopRecording()
            }
            return true
        }
    }
    
    func getSession() -> NSObject {
        
        while session.inputs.count < 2 {
            print("...")
            usleep(1000)
        }

        return session
    }
    
    func startRecording(username: String, sceneDescription: String, sceneType: String) {
        
        sessionQueue.async { [self] in
            
            self.username = username
            self.sceneDescription = sceneDescription
            self.sceneType = sceneType
            
            primaryVideoRecordingFinished = false
            secondaryVideoRecordingFinished = false
            
            gpsLocation = Helper.getGpsLocation(locationManager: locationManager)
            
            recordingId = Helper.getRecordingId()
            dirUrl = URL(fileURLWithPath: Helper.getRecordingDataDirectoryPath(recordingId: recordingId))
            
            // Motion data
            motionManager.startRecording(dataPathString: dirUrl.path, recordingId: recordingId)
            
            // Video
            let primaryVideoFilename = recordingId + "-primary"
            primaryVideoFilePath = (dirUrl.path as NSString).appendingPathComponent((primaryVideoFilename as NSString).appendingPathExtension("mp4")!)
            
            let secondaryVideoFilename = recordingId + "-secondary"
            secondaryVideoFilePath = (dirUrl.path as NSString).appendingPathComponent((secondaryVideoFilename as NSString).appendingPathExtension("mp4")!)
            
            self.primaryCameraOutput.startRecording(to: URL(fileURLWithPath: primaryVideoFilePath), recordingDelegate: self)
            self.secondaryCameraOutput.startRecording(to: URL(fileURLWithPath: secondaryVideoFilePath), recordingDelegate: self)
    
        }

    }
    
    func stopRecording() {
        
        sessionQueue.async {
            self.primaryCameraOutput.stopRecording()
            self.secondaryCameraOutput.stopRecording()
        }
        
    }

}

@available(iOS 13.0, *)
extension DualCameraRecordingManager: AVCaptureFileOutputRecordingDelegate {
    /// write camera metadata to file
    func fileOutput(_ output: AVCaptureFileOutput, didFinishRecordingTo outputFileURL: URL, from connections: [AVCaptureConnection], error: Error?) {
        
        if error != nil {
            print("Movie file finishing error: \(String(describing: error))")
        }

        sessionQueue.async { [self] in
            
            if outputFileURL.path == primaryVideoFilePath {
                primaryVideoRecordingFinished = true
                print("primary video ready")
            } else if outputFileURL.path == secondaryVideoFilePath {
                secondaryVideoRecordingFinished = true
                print("secondary video ready")
            }
            
            if primaryVideoRecordingFinished && secondaryVideoRecordingFinished {
                
                var streamInfo: [StreamInfo] = motionManager.stopRecordingAndReturnStreamInfo()

                let primaryVideoNumberOfFrames = VideoHelper.getNumberOfFrames(videoUrl: URL(fileURLWithPath: primaryVideoFilePath))
                let primaryCameraStreamInfo = CameraStreamInfo(id: "color_back_1", type: "color_camera", encoding: "h264", frequency: primaryCameraFramerate, numberOfFrames: primaryVideoNumberOfFrames, fileExtension: "mp4", resolution: primaryCameraResolution, intrinsics: primaryCameraIntrinsicArray, extrinsics: extrinsicsPrimaryToSecondary)
                streamInfo.append(primaryCameraStreamInfo)
                
                let secondaryVideoNumberOfFrames = VideoHelper.getNumberOfFrames(videoUrl: URL(fileURLWithPath: secondaryVideoFilePath))
                let secondaryCameraStreamInfo = CameraStreamInfo(id: "color_back_2", type: "color_camera", encoding: "h264", frequency: secondaryCameraFramerate, numberOfFrames: secondaryVideoNumberOfFrames, fileExtension: "mp4", resolution: secondaryCameraResolution, intrinsics: secondaryCameraIntrinsicArray, extrinsics: extrinsicsSecondaryToPrimary)
                streamInfo.append(secondaryCameraStreamInfo)

                let metadata = Metadata(username: username ?? "", userInputDescription: sceneDescription ?? "", sceneType: sceneType ?? "", gpsLocation: gpsLocation, streams: streamInfo, numberOfFiles: 8)

                let metadataPath = (dirUrl.path as NSString).appendingPathComponent((recordingId as NSString).appendingPathExtension("json")!)

                metadata.display()
                metadata.writeToFile(filepath: metadataPath)

                username = nil
                sceneDescription = nil
                sceneType = nil
            }

        }
    }
    
    
}
