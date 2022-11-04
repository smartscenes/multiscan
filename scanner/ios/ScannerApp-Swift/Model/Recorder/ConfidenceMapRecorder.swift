//
//  ConfidenceMapRecorder.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-10-27.
//  Copyright © 2020 jx16. All rights reserved.
//

import Accelerate.vImage
import CoreMedia
import CoreVideo
import Foundation
import Compression
import UIKit

class ConfidenceMapRecorder: Recorder {
    typealias T = CVPixelBuffer
    
    private let confidenceMapRecorderQueue = DispatchQueue(label: "confidence map recorder queue")
    
	private var compressedFileHandle: FileHandle? = nil
	private var compressedFileUrl: URL? = nil
    
    private var count: Int32 = 0

	private var compressor: Compressor?
    
    func prepareForRecording(dirPath: String, filename: String, fileExtension: String = "confidence") {
        
        confidenceMapRecorderQueue.async {
            
            self.count = 0
            
            let filePath = (dirPath as NSString).appendingPathComponent((filename as NSString).appendingPathExtension(fileExtension)!)
            let compressedFilePath = (filePath as NSString).appendingPathExtension("zlib")!
            
			self.compressedFileUrl = URL(fileURLWithPath: compressedFilePath)
			FileManager.default.createFile(atPath: self.compressedFileUrl!.path, contents: nil, attributes: nil)
			self.compressedFileHandle = FileHandle(forUpdatingAtPath: self.compressedFileUrl!.path)
			if self.compressedFileHandle == nil {
				print("Unable to create compressed file handle.")
				return
			}
			
			self.compressor = Compressor(operation: .compression, algorithm: .zlib)
        }
        
    }
    
    /// update and save the confidence map for one frame
    func update(_ buffer: CVPixelBuffer, timestamp: CMTime? = nil) {
        
        confidenceMapRecorderQueue.async {
            
            print("Saving confidence map \(self.count) ...")
            
            CVPixelBufferLockBaseAddress(buffer, .readOnly)
            
            let baseAddress: UnsafeMutableRawPointer = CVPixelBufferGetBaseAddress(buffer)!
            let size = CVPixelBufferGetDataSize(buffer)
            let data = Data(bytesNoCopy: baseAddress, count: size, deallocator: .none)
			let compressed = self.compressor?.perform(input: data)
			self.compressedFileHandle?.write(compressed!)
            
            CVPixelBufferUnlockBaseAddress(buffer, .readOnly)
            
            self.count += 1
        }
        
    }
    
    func finishRecording() {
        
        confidenceMapRecorderQueue.async {
            print("\(self.count) confidence maps saved.")
            self.compressFinished()
        }
        
    }
    
    // below are duplicate with code in DepthRecorder, consider refactor
    // this method is based on apple's sample app Compression-Streaming-Sample
    /// No longer used
    private func compressFinished() {
		let compressed = self.compressor?.finish()
		self.compressedFileHandle?.write(compressed!)
		
		if self.compressedFileHandle != nil {
			self.compressedFileHandle!.closeFile()
			self.compressedFileHandle = nil
		}
        UIApplication.shared.presentAlertOnTopViewController(message: "Confidence value compressed.")
    }
}
