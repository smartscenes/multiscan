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

class CameraInfo: Encodable {
    
    private var timestamp: Int64
    private var intrinsics: simd_float3x3
    private var transform: simd_float4x4
    private var eulerAngles: simd_float3
    private var exposureDuration: Int64
    
    internal init(timestamp: TimeInterval, intrinsics: simd_float3x3, transform: simd_float4x4, eulerAngles: simd_float3, exposureDuration: TimeInterval) {
        self.timestamp = Int64(timestamp * 1_000_000_000.0)
        self.intrinsics = intrinsics
        self.transform = transform
        self.eulerAngles = eulerAngles
        self.exposureDuration = Int64(exposureDuration * 1_000_000_000.0)
    }
    
    func getJsonEncoding() -> String {
        let encoder = JSONEncoder()
//        encoder.outputFormatting = .prettyPrinted
        encoder.keyEncodingStrategy = .convertToSnakeCase
        
        let data = try! encoder.encode(self)
        return String(data: data, encoding: .utf8)!
    }
}

class CameraInfoRecorder: Recorder {
    typealias T = CameraInfo
    
    private let cameraInfoQueue = DispatchQueue(label: "camera info queue")
    
    private var fileHandle: FileHandle? = nil
    private var fileUrl: URL? = nil
    
    private var count: Int32 = 0
    
    func prepareForRecording(dirPath: String, filename: String, fileExtension: String = "jsonl") {
        
        cameraInfoQueue.async {
            
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
    
    func update(_ cameraInfo: CameraInfo, timestamp: CMTime? = nil) {
        cameraInfoQueue.async {
            print("Saving camera info \(self.count) ...")
            
//            print(cameraInfo.getJsonEncoding())
            self.fileHandle?.write((cameraInfo.getJsonEncoding() + "\n").data(using: .utf8)!)
            
            self.count += 1
        }
    }
    
    func finishRecording() {
        cameraInfoQueue.async {
            if self.fileHandle != nil {
                self.fileHandle!.closeFile()
                self.fileHandle = nil
            }
            
            print("\(self.count) frames of camera info saved.")
        }
    }
}
