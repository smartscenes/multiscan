//
//  CameraInfoRecorder.swift
//  LiDARDepth
//
//  Created by Zheren Xiao on 2020-10-08.
//  Copyright © 2020 jx16. All rights reserved.
//

import CoreMedia
import Foundation
import simd

/// camera info data holder
class CameraInfo: Encodable {
    
    private var timestamp: Int64
    private var intrinsics: simd_float3x3
    private var transform: simd_float4x4
    private var eulerAngles: simd_float3 // Pitch(x) Yaw(y) Roll(z)
    private var exposureDuration: Int64
    private var quaternion: simd_float4
    
    internal init(timestamp: TimeInterval, intrinsics: simd_float3x3, transform: simd_float4x4, eulerAngles: simd_float3, exposureDuration: TimeInterval) {
        self.timestamp = Int64(timestamp * 1_000_000_000.0)
        self.intrinsics = intrinsics
        self.transform = transform
        self.eulerAngles = eulerAngles
        self.quaternion = CameraInfo.toQuaternion(eulerAngles: eulerAngles)

        self.exposureDuration = Int64(exposureDuration * 1_000_000_000.0)
    }
    
    /// get camera info in json format
    func getJsonEncoding() -> String {
        let encoder = JSONEncoder()
//        encoder.outputFormatting = .prettyPrinted
        encoder.keyEncodingStrategy = .convertToSnakeCase
        
        let data = try! encoder.encode(self)
        return String(data: data, encoding: .utf8)!
    }

    // convert eulerAngles to Quaternion
    static func toQuaternion(eulerAngles: simd_float3) -> simd_float4 {
        let eulerAnglesX = eulerAngles[0]
        let eulerAnglesY = eulerAngles[1]
        let eulerAnglesZ = eulerAngles[2]

        let cosX = cos(eulerAnglesX * 0.5)
        let sinX = sin(eulerAnglesX * 0.5)
        let cosY = cos(eulerAnglesY * 0.5)
        let sinY = sin(eulerAnglesY * 0.5)
        let cosZ = cos(eulerAnglesZ * 0.5)
        let sinZ = sin(eulerAnglesZ * 0.5)

        let w = cosX * cosY * cosZ + sinX * sinY * sinZ;
        let x = sinX * cosY * cosZ - cosX * sinY * sinZ;
        let y = cosX * sinY * cosZ + sinX * cosY * sinZ;
        let z = cosX * cosY * sinZ - sinX * sinY * cosZ;
        
        return simd_float4(w, x, y, z)
    }
}

/// retrieve camera info such as intrinsic and timestamp etc.
class CameraInfoRecorder: Recorder {
    typealias T = CameraInfo
    
    private let cameraInfoRecorderQueue = DispatchQueue(label: "camera info recorder queue")
    
    private var fileHandle: FileHandle? = nil
    private var fileUrl: URL? = nil
    
    private var count: Int32 = 0
    
    func prepareForRecording(dirPath: String, filename: String, fileExtension: String = "jsonl") {
        
        cameraInfoRecorderQueue.async {
            
            self.count = 0
            
            let filePath = (dirPath as NSString).appendingPathComponent((filename as NSString).appendingPathExtension(fileExtension)!)
            self.fileUrl = URL(fileURLWithPath: filePath)
            FileManager.default.createFile(atPath: self.fileUrl!.path, contents: nil, attributes: nil)
            
            self.fileHandle = FileHandle(forUpdatingAtPath: self.fileUrl!.path)
            if self.fileHandle == nil {
                print("Unable to create file handle.")
                return
            }
        }
        
    }
    
    /// Update and save the camera info for one frame
    func update(_ cameraInfo: CameraInfo, timestamp: CMTime? = nil) {
        cameraInfoRecorderQueue.async {
            print("Saving camera info \(self.count) ...")
            
//            print(cameraInfo.getJsonEncoding())
            self.fileHandle?.write((cameraInfo.getJsonEncoding() + "\n").data(using: .utf8)!)
            
            self.count += 1
        }
    }
    
    func finishRecording() {
        cameraInfoRecorderQueue.async {
            if self.fileHandle != nil {
                self.fileHandle!.closeFile()
                self.fileHandle = nil
            }
            
            print("\(self.count) frames of camera info saved.")
        }
    }
}
