//
//  ARCameraRecordingManager.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-11-17.
//  Copyright © 2020 jx16. All rights reserved.
//

import ARKit

@available(iOS 14.0, *)
class ARCameraRecordingManager: NSObject {
    
    private let sessionQueue = DispatchQueue(label: "ar camera recording queue")
    
    private let session = ARSession()
    
    private let depthRecorder = DepthRecorder()
    private let confidenceMapRecorder = ConfidenceMapRecorder()
    private var rgbRecorder: RGBRecorder! = nil // rgbRecorder will be initialized in configureSession
    private let cameraInfoRecorder = CameraInfoRecorder()
    
    private var numFrames: Int = 0
    private var dirUrl: URL!
    private var recordingId: String!
    var isRecording: Bool = false
    
    private let locationManager = CLLocationManager()
    private var gpsLocation: [Double] = []
    
    private var cameraIntrinsic: simd_float3x3?
    private var colorFrameResolution: [Int] = []
    private var depthFrameResolution: [Int] = []
    private var frequency: Int?
    
    private var username: String?
    private var sceneDescription: String?
    private var sceneType: String?
    
    override init() {
        super.init()
        
        locationManager.requestWhenInUseAuthorization()
        
        sessionQueue.async {
            self.configureSession()
        }
    }
    
    deinit {
        sessionQueue.sync {
            session.pause()
        }
    }
    
    private func configureSession() {
        session.delegate = self
        
        let configuration = ARWorldTrackingConfiguration()
        configuration.frameSemantics = .sceneDepth
        session.run(configuration)
        
        let videoFormat = configuration.videoFormat
        frequency = videoFormat.framesPerSecond
        let imageResolution = videoFormat.imageResolution
        colorFrameResolution = [Int(imageResolution.height), Int(imageResolution.width)]
        
        let videoSettings: [String: Any] = [AVVideoCodecKey: AVVideoCodecType.h264, AVVideoHeightKey: NSNumber(value: colorFrameResolution[0]), AVVideoWidthKey: NSNumber(value: colorFrameResolution[1])]
        rgbRecorder = RGBRecorder(videoSettings: videoSettings)
    }
}

@available(iOS 14.0, *)
extension ARCameraRecordingManager: RecordingManager {
    
    func getSession() -> NSObject {
        return session
    }
    
    func startRecording(username: String, sceneDescription: String, sceneType: String) {
        
        sessionQueue.async { [self] in
            
            self.username = username
            self.sceneDescription = sceneDescription
            self.sceneType = sceneType
            
            gpsLocation = Helper.getGpsLocation(locationManager: locationManager)
            
            numFrames = 0
            
            // TODO: consider an if check here to avoid doing this for every recording?
            if let currentFrame = session.currentFrame {
                cameraIntrinsic = currentFrame.camera.intrinsics
                
                // get depth resolution
                if let depthData = currentFrame.sceneDepth {
                    
                    let depthMap: CVPixelBuffer = depthData.depthMap
                    let height = CVPixelBufferGetHeight(depthMap)
                    let width = CVPixelBufferGetWidth(depthMap)
                    
                    depthFrameResolution = [height, width]
                    
                } else {
                    print("Unable to get depth resolution.")
                }
                
            }
            
            print("pre1 count: \(numFrames)")
            
            recordingId = Helper.getRecordingId()
            dirUrl = URL(fileURLWithPath: Helper.getRecordingDataDirectoryPath(recordingId: recordingId))
            
            depthRecorder.prepareForRecording(dirPath: dirUrl.path, filename: recordingId)
            confidenceMapRecorder.prepareForRecording(dirPath: dirUrl.path, filename: recordingId)
            rgbRecorder.prepareForRecording(dirPath: dirUrl.path, filename: recordingId)
            cameraInfoRecorder.prepareForRecording(dirPath: dirUrl.path, filename: recordingId)
            
            isRecording = true
            
            print("pre2 count: \(numFrames)")
        }
        
    }
    
    func stopRecording() {
        
        sessionQueue.sync { [self] in
            
            print("post count: \(numFrames)")
            
            isRecording = false
            
            depthRecorder.finishRecording()
            confidenceMapRecorder.finishRecording()
            rgbRecorder.finishRecording()
            cameraInfoRecorder.finishRecording()
            
            writeMetadataToFile()
            
            username = nil
            sceneDescription = nil
            sceneType = nil
            
        }
    }
    
    private func writeMetadataToFile() {
        
        let cameraIntrinsicArray = cameraIntrinsic?.arrayRepresentation
        let rgbStreamInfo = CameraStreamInfo(id: "color_back_1", type: "color_camera", encoding: "h264", frequency: frequency ?? 0, numberOfFrames: numFrames, fileExtension: "mp4", resolution: colorFrameResolution, intrinsics: cameraIntrinsicArray, extrinsics: nil)
        let depthStreamInfo = CameraStreamInfo(id: "depth_back_1", type: "lidar_sensor", encoding: "float16_zlib", frequency: frequency ?? 0, numberOfFrames: numFrames, fileExtension: "depth.zlib", resolution: depthFrameResolution, intrinsics: nil, extrinsics: nil)
        let confidenceMapStreamInfo = StreamInfo(id: "confidence_map", type: "confidence_map", encoding: "uint8_zlib", frequency: frequency ?? 0, numberOfFrames: numFrames, fileExtension: "confidence.zlib")
        let cameraInfoStreamInfo = StreamInfo(id: "camera_info_color_back_1", type: "camera_info", encoding: "jsonl", frequency: frequency ?? 0, numberOfFrames: numFrames, fileExtension: "jsonl")
        
        let metadata = Metadata(username: username ?? "", userInputDescription: sceneDescription ?? "", sceneType: sceneType ?? "", gpsLocation: gpsLocation, streams: [rgbStreamInfo, depthStreamInfo, confidenceMapStreamInfo, cameraInfoStreamInfo], numberOfFiles: 5)

        let metadataPath = (dirUrl.path as NSString).appendingPathComponent((recordingId as NSString).appendingPathExtension("json")!)
        
        metadata.display()
        metadata.writeToFile(filepath: metadataPath)
    }
    
}

@available(iOS 14.0, *)
extension ARCameraRecordingManager: ARSessionDelegate {
    
    func session(_ session: ARSession, didUpdate frame: ARFrame) {

        if !isRecording {
            return
        }
        
        guard let depthData = frame.sceneDepth else {
            print("Failed to acquire depth data.")
            return
        }

        let depthMap: CVPixelBuffer = depthData.depthMap
        let colorImage: CVPixelBuffer = frame.capturedImage
        
        guard let confidenceMap = depthData.confidenceMap else {
            print("Failed to get confidenceMap.")
            return
        }

        let timestamp: CMTime = CMTime(seconds: frame.timestamp, preferredTimescale: 1_000_000_000)

        print("**** @Controller: depth \(numFrames) ****")
        depthRecorder.update(depthMap)

        print("**** @Controller: confidence \(numFrames) ****")
        confidenceMapRecorder.update(confidenceMap)
        
        print("**** @Controller: color \(numFrames) ****")
        rgbRecorder.update(colorImage, timestamp: timestamp)
        print()
    
        let currentCameraInfo = CameraInfo(timestamp: frame.timestamp,
                                           intrinsics: frame.camera.intrinsics,
                                           transform: frame.camera.transform,
                                           eulerAngles: frame.camera.eulerAngles,
                                           exposureDuration: frame.camera.exposureDuration)
        cameraInfoRecorder.update(currentCameraInfo)
        
        numFrames += 1
    }
}

