//
//  ConfidenceMapRecorder.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-10-27.
//  Copyright © 2020 jx16. All rights reserved.
//

import Accelerate.vImage
import Compression
import CoreMedia
import CoreVideo
import Foundation

class ConfidenceMapRecorder: Recorder {
    typealias T = CVPixelBuffer
    
    private let confidenceMapQueue = DispatchQueue(label: "confidence map queue")
    
    private var fileHandle: FileHandle? = nil
    private var fileUrl: URL? = nil
    private var compressedFileUrl: URL? = nil
    
    private var count: Int32 = 0
    
    func prepareForRecording(dirPath: String, filename: String, fileExtension: String = "confidence") {
        
        confidenceMapQueue.async {
            
            self.count = 0
            
            let filePath = (dirPath as NSString).appendingPathComponent((filename as NSString).appendingPathExtension(fileExtension)!)
            let compressedFilePath = (filePath as NSString).appendingPathExtension("zlib")!
            self.fileUrl = URL(fileURLWithPath: filePath)
            self.compressedFileUrl = URL(fileURLWithPath: compressedFilePath)
            FileManager.default.createFile(atPath: self.fileUrl!.path, contents: nil, attributes: nil)
            
            self.fileHandle = FileHandle(forUpdatingAtPath: self.fileUrl!.path)
            if self.fileHandle == nil {
                print("Unable to create file handle.")
                return
            }
        }
        
    }
    
    func update(_ buffer: CVPixelBuffer, timestamp: CMTime? = nil) {
        
        confidenceMapQueue.async {
            
            print("Saving confidence map \(self.count) ...")
            
            CVPixelBufferLockBaseAddress(buffer, .readOnly)
            
            let baseAddress: UnsafeMutableRawPointer = CVPixelBufferGetBaseAddress(buffer)!
            let size = CVPixelBufferGetDataSize(buffer)
            let data = Data(bytesNoCopy: baseAddress, count: size, deallocator: .none)
            self.fileHandle?.write(data)
            
            CVPixelBufferUnlockBaseAddress(buffer, .readOnly)
            
            self.count += 1
        }
        
    }
    
    func finishRecording() {
        
        confidenceMapQueue.async {
            if self.fileHandle != nil {
                self.fileHandle!.closeFile()
                self.fileHandle = nil
            }
            
            print("\(self.count) confidence maps saved.")
            
            self.compressFile()
            self.removeUncompressedFile()
            
        }
        
    }
    
    // below are duplicate with code in DepthRecorder, consider refactor
    // this method is based on apple's sample app Compression-Streaming-Sample
    private func compressFile() {
        
        let algorithm = COMPRESSION_ZLIB
        let operation = COMPRESSION_STREAM_ENCODE
        
//        let compressedFilePath = (fileUrl!.path as NSString).appendingPathExtension("zlib")!
//        let compressedFileUrl = URL(fileURLWithPath: compressedFilePath)
        
        FileManager.default.createFile(atPath: compressedFileUrl!.path, contents: nil, attributes: nil)
        
        if let sourceFileHandle = try? FileHandle(forReadingFrom: fileUrl!),
           let destinationFileHandle = try? FileHandle(forWritingTo: compressedFileUrl!) {
            
            Compressor.streamingCompression(operation: operation,
                                            sourceFileHandle: sourceFileHandle,
                                            destinationFileHandle: destinationFileHandle,
                                            algorithm: algorithm) {
                                                print($0)
            }
        }
    }
    
    private func removeUncompressedFile() {
        do {
            try FileManager.default.removeItem(at: fileUrl!)
            print("Uncompressed depth file \(fileUrl!.lastPathComponent) removed.")
        } catch {
            print("Unable to remove uncompressed depth file.")
        }
    }
    
}
