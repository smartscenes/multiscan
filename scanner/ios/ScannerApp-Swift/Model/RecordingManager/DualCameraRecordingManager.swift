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
    
//    private let dataOutputQueue = DispatchQueue(label: "data output queue")

//    private var isRecording = false
    
    private var dirUrl: URL!
    private var recordingId: String!
    private var mainVideoFilePath: String!
    private var secondaryVideoFilePath: String!
    
    private let locationManager = CLLocationManager()
    private var gpsLocation: [Double] = []
    
    private var extrinsics: Data?
    
    private var mainCameraInput: AVCaptureDeviceInput?
    private let mainCameraOutput = AVCaptureMovieFileOutput()
    
    private var secondaryCameraInput: AVCaptureDeviceInput?
    private let secondaryCameraOutput = AVCaptureMovieFileOutput()
    
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
        
        session.beginConfiguration()
        defer {
            session.commitConfiguration()
        }
        
        // Get devices
        guard let mainCameraDevice = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back) else {
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
        
//        if let wide = AVCaptureDevice.default(.builtInWideAngleCamera, for: nil, position: .back), let tele = AVCaptureDevice.default(.builtInTelephotoCamera, for: nil, position: .back) {
//            self.extrinsics = AVCaptureDevice.extrinsicMatrix(from: tele, to: wide)
//
//            let matrix: matrix_float4x3 = self.extrinsics!.withUnsafeBytes { $0.pointee }
//
//            print(matrix)
//        }
        
        
        // Add input
        do {
            mainCameraInput = try AVCaptureDeviceInput(device: mainCameraDevice)
            
            guard let mainCameraInput = mainCameraInput, session.canAddInput(mainCameraInput) else {
                print("Could not add wide angle camera device input")
                return
            }
            
            session.addInputWithNoConnections(mainCameraInput)
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
        guard session.canAddOutput(mainCameraOutput) else {
            print("Could not add wide-angle camera output")
            return
        }
        session.addOutputWithNoConnections(mainCameraOutput)
        
        guard session.canAddOutput(secondaryCameraOutput) else {
            print("Could not add secondary camera output")
            return
        }
        session.addOutputWithNoConnections(secondaryCameraOutput)
        
        // Setup input/output connection
        guard let mainCameraPort = mainCameraInput!.ports(for: .video,
                                                   sourceDeviceType: .builtInWideAngleCamera,
                                                   sourceDevicePosition: mainCameraDevice.position).first
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
        
        let mainCameraConnection = AVCaptureConnection(inputPorts: [mainCameraPort], output: mainCameraOutput)
        guard session.canAddConnection(mainCameraConnection) else {
            print("Cannot add wide-angle input to output")
            return
        }
        session.addConnection(mainCameraConnection)
        mainCameraConnection.videoOrientation = .landscapeRight
        
        let mainCameraAvailableVideoCodecTypes = mainCameraOutput.availableVideoCodecTypes
        if mainCameraAvailableVideoCodecTypes.contains(.h264) {
            mainCameraOutput.setOutputSettings([AVVideoCodecKey: AVVideoCodecType.h264], for: mainCameraConnection)
        }
        
        let secondaryCameraConnection = AVCaptureConnection(inputPorts: [secondaryCameraPort], output: secondaryCameraOutput)
        guard session.canAddConnection(secondaryCameraConnection) else {
            print("Cannot add secondary input to output")
            return
        }
        session.addConnection(secondaryCameraConnection)
        secondaryCameraConnection.videoOrientation = .landscapeRight
        
        let secondaryCameraAvailableVideoCodecTypes = mainCameraOutput.availableVideoCodecTypes
        if secondaryCameraAvailableVideoCodecTypes.contains(.h264) {
            mainCameraOutput.setOutputSettings([AVVideoCodecKey: AVVideoCodecType.h264], for: mainCameraConnection)
        }
        
    }
}

@available(iOS 13.0, *)
extension DualCameraRecordingManager: RecordingManager {
    
    var isRecording: Bool {
        
        // TODO: Should these be check in the session queue??
        if mainCameraOutput.isRecording && secondaryCameraOutput.isRecording {
            return true
        } else if !mainCameraOutput.isRecording && !secondaryCameraOutput.isRecording {
            return false
        } else {
            print("MultiCam session is at unexpected state")
            
            if mainCameraOutput.isRecording {
                mainCameraOutput.stopRecording()
            }
            if secondaryCameraOutput.isRecording {
                secondaryCameraOutput.stopRecording()
            }
            return true
        }
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
            
            // Motion data
            motionManager.startRecording(dataPathString: dirUrl.path, recordingId: recordingId)
            
            // Video
            let mainVideoFilename = recordingId + "-main"
            mainVideoFilePath = (dirUrl.path as NSString).appendingPathComponent((mainVideoFilename as NSString).appendingPathExtension("mp4")!)
            
            let secondaryVideoFilename = recordingId + "-secondary"
            secondaryVideoFilePath = (dirUrl.path as NSString).appendingPathComponent((secondaryVideoFilename as NSString).appendingPathExtension("mp4")!)
            
            self.mainCameraOutput.startRecording(to: URL(fileURLWithPath: mainVideoFilePath), recordingDelegate: self)
            self.secondaryCameraOutput.startRecording(to: URL(fileURLWithPath: secondaryVideoFilePath), recordingDelegate: self)
    
        }

    }
    
    func stopRecording() {
        
        sessionQueue.async {
            self.mainCameraOutput.stopRecording()
            self.secondaryCameraOutput.stopRecording()
            
            // TODO: temporarily put here
            self.motionManager.stopRecordingAndReturnStreamInfo()
        }
        
    }

}

@available(iOS 13.0, *)
extension DualCameraRecordingManager: AVCaptureFileOutputRecordingDelegate {
    
    func fileOutput(_ output: AVCaptureFileOutput, didFinishRecordingTo outputFileURL: URL, from connections: [AVCaptureConnection], error: Error?) {
        
        if outputFileURL.path == mainVideoFilePath {
            print("main video ready")
        } else if outputFileURL.path == secondaryVideoFilePath {
            print("secondary video ready")
        }
        
        // TODO:
    }
    
    
}
