//
//  DepthRecorder.swift
//  LiDARDepth
//
//  Created by Zheren Xiao on 2020-09-21.
//  Copyright © 2020 jx16. All rights reserved.
//

import Accelerate.vImage
import CoreMedia
import CoreVideo
import Foundation
import Compression
import UIKit


class DepthRecorder: Recorder {
    typealias T = CVPixelBuffer
    
    private let depthRecorderQueue = DispatchQueue(label: "depth recorder queue")
    
	private var compressedFileHandle: FileHandle? = nil
    private var compressedFileUrl: URL? = nil
    
    private var count: Int32 = 0
	
	private var compressor: Compressor?
    
    func prepareForRecording(dirPath: String, filename: String, fileExtension: String = "depth") {
        
		depthRecorderQueue.async { [self] in
            
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
    
    /// record and save the depth info for one frame (this function will also convert the depth map from float32 to flaot16)
    func update(_ buffer: CVPixelBuffer, timestamp: CMTime? = nil) {
        
        depthRecorderQueue.async {
            
            print("Saving frame \(self.count) ...")
            
//            self.writePixelBufferToFile(buffer: buffer)
//            self.convertF32DepthMapToF16PixelByPixelAndWriteToFile(buffer: buffer)
            self.convertF32DepthMapToF16AndWriteToFile(f32CVPixelBuffer: buffer)
            
            self.count += 1
        }
        
    }
    
    func updateWithoutConversion(_ buffer: CVPixelBuffer) {
        
        depthRecorderQueue.async {
            
            print("Saving depth frame \(self.count) ...")
            
//            self.writePixelBufferToFile(buffer: buffer)
            
            CVPixelBufferLockBaseAddress(buffer, .readOnly)

            let baseAddress: UnsafeMutableRawPointer = CVPixelBufferGetBaseAddress(buffer)!
            
            let bytePerRow = CVPixelBufferGetBytesPerRow(buffer)
            let height = CVPixelBufferGetHeight(buffer)
//            let width = CVPixelBufferGetWidth(buffer)
            let size = bytePerRow * height
            
//            let size = CVPixelBufferGetDataSize(buffer)
            
            let data = Data(bytesNoCopy: baseAddress, count: size, deallocator: .none)
			let compressed = self.compressor?.perform(input: data)
			self.compressedFileHandle?.write(compressed!)

            CVPixelBufferUnlockBaseAddress(buffer, .readOnly)
            
            self.count += 1
        }
        
    }
    
    func finishRecording() {
        
        depthRecorderQueue.async {
            print("\(self.count) frames saved.")
            
            self.compressFinished()
            
        }
        
    }
    
    /// Display buffer info to console
    func displayBufferInfo(buffer: CVPixelBuffer) {
        
        depthRecorderQueue.async {
            let type = CVPixelBufferGetPixelFormatType(buffer)
            
            let size = CVPixelBufferGetDataSize(buffer)
            let height = CVPixelBufferGetHeight(buffer)
            let width = CVPixelBufferGetWidth(buffer)
            let numPlane = CVPixelBufferGetPlaneCount(buffer)
            
            let bytePerRow = CVPixelBufferGetBytesPerRow(buffer)
            
            print("type: \(type)")
            print("size: \(size)")
            print("height: \(height)")
            print("width: \(width)")
            print("numPlane: \(numPlane)")
            print("bytePerRow: \(bytePerRow)")
            
//            displayDepthValues(buffer: buffer)
        }
        
    }
    
    // TODO: Float16 is available in iOS 14.0 or newer, which is unexpected, need to consider alternative if this method is needed
    /// Display depth values to console
    @available(iOS 14.0, *)
    private func displayDepthValues(buffer: CVPixelBuffer) {
        CVPixelBufferLockBaseAddress(buffer, .readOnly)
        
        let baseAddress: UnsafeMutableRawPointer = CVPixelBufferGetBaseAddress(buffer)!
        
        let height = CVPixelBufferGetHeight(buffer)
        let width = CVPixelBufferGetWidth(buffer)
        let numPixel = height * width
        
        for i in 0..<numPixel {
            let f32 = baseAddress.load(fromByteOffset: i*4, as: Float32.self)
            print("32-bit depth[\(i)] in meter: \(f32)")
            let f16 = Float16(f32)
            print("16-bit depth[\(i)] in meter: \(f16)")
        }
        
        CVPixelBufferUnlockBaseAddress(buffer, .readOnly)
    }
    
    private func writePixelBufferToFile(buffer: CVPixelBuffer) {
        CVPixelBufferLockBaseAddress(buffer, .readOnly)

        let baseAddress: UnsafeMutableRawPointer = CVPixelBufferGetBaseAddress(buffer)!
        let size = CVPixelBufferGetDataSize(buffer)
        let data = Data(bytesNoCopy: baseAddress, count: size, deallocator: .none)
		let compressed = self.compressor?.perform(input: data)
		self.compressedFileHandle?.write(compressed!)

        CVPixelBufferUnlockBaseAddress(buffer, .readOnly)
    }
    
    /// convert depth values from float32 to float16 and save the values
    @available(iOS 14.0, *)
    private func convertF32DepthMapToF16PixelByPixelAndWriteToFile(buffer: CVPixelBuffer) {
        CVPixelBufferLockBaseAddress(buffer, .readOnly)
        
        let baseAddress: UnsafeMutableRawPointer = CVPixelBufferGetBaseAddress(buffer)!
        
        let height = CVPixelBufferGetHeight(buffer)
        let width = CVPixelBufferGetWidth(buffer)
        let numPixel = height * width
        let f16Pointer = UnsafeMutableRawPointer.allocate(byteCount: numPixel*2, alignment: 1)
        
        for i in 0..<numPixel {
            let f32 = baseAddress.load(fromByteOffset: i*4, as: Float32.self)
            f16Pointer.storeBytes(of: Float16(f32), toByteOffset: i*2, as: Float16.self)
        }
		
		let data = Data(bytes: f16Pointer, count: numPixel*2)
		let compressed = self.compressor?.perform(input: data)
		self.compressedFileHandle?.write(compressed!)
        
        f16Pointer.deallocate()
        
        CVPixelBufferUnlockBaseAddress(buffer, .readOnly)
    }
    
    /// convert depth values from float32 to float16 and save the values
    private func convertF32DepthMapToF16AndWriteToFile(f32CVPixelBuffer: CVPixelBuffer) {
        
        CVPixelBufferLockBaseAddress(f32CVPixelBuffer, .readOnly)
        
        let height = CVPixelBufferGetHeight(f32CVPixelBuffer)
        let width = CVPixelBufferGetWidth(f32CVPixelBuffer)
        let numPixel = height * width
        
        var f32vImageBuffer = vImage_Buffer()
        f32vImageBuffer.data = CVPixelBufferGetBaseAddress(f32CVPixelBuffer)!
        f32vImageBuffer.height = UInt(height)
        f32vImageBuffer.width = UInt(width)
        f32vImageBuffer.rowBytes = CVPixelBufferGetBytesPerRow(f32CVPixelBuffer)
        
        var error = kvImageNoError
        
        var f16vImageBuffer = vImage_Buffer()
        error = vImageBuffer_Init(&f16vImageBuffer,
                                  f32vImageBuffer.height,
                                  f32vImageBuffer.width,
                                  16,
                                  vImage_Flags(kvImageNoFlags))
        
        guard error == kvImageNoError else {
            print("Unable to init destination vImagebuffer.")
            return
        }
        defer {
            free(f16vImageBuffer.data)
        }
        
        error = vImageConvert_PlanarFtoPlanar16F(&f32vImageBuffer,
                                                 &f16vImageBuffer,
                                                 vImage_Flags(kvImagePrintDiagnosticsToConsole))
        
        guard error == kvImageNoError else {
            print("Unable to convert.")
            return
        }
        
//        for i in (numPixel - 10) ..< numPixel {
//            let f32 = f32vImageBuffer.data.load(fromByteOffset: i*4, as: Float32.self)
//            print("32-bit depth[\(i)] in meter: \(f32)")
//            let f16 = f16vImageBuffer.data.load(fromByteOffset: i*2, as: Float16.self)
//            print("16-bit depth[\(i)] in meter: \(f16)")
//        }
		let data = Data(bytesNoCopy: f16vImageBuffer.data, count: numPixel * 2, deallocator: .none)
		let compressed = self.compressor?.perform(input: data)
		self.compressedFileHandle?.write(compressed!)
        
        CVPixelBufferUnlockBaseAddress(f32CVPixelBuffer, .readOnly)
        
    }
    
    // this method is based on apple's sample app Compression-Streaming-Sample
    /// this method is based on apple's sample app Compression-Streaming-Sample
    private func compressFinished() {
		let compressed = self.compressor?.finish()
		self.compressedFileHandle?.write(compressed!)
		
		if self.compressedFileHandle != nil {
			self.compressedFileHandle!.closeFile()
			self.compressedFileHandle = nil
		}
        UIApplication.shared.presentAlertOnTopViewController(message: "Depth value compressed.")
    }
}

/// generate a pop up window to the user
extension UIApplication {
    private func topViewController(controller: UIViewController? = UIApplication.shared.keyWindow?.rootViewController) -> UIViewController? {
        if let navigationController = controller as? UINavigationController {
            return topViewController(controller: navigationController.visibleViewController)
        }
        if let tabController = controller as? UITabBarController {
            if let selected = tabController.selectedViewController {
                return topViewController(controller: selected)
            }
        }
        if let presented = controller?.presentedViewController {
            return topViewController(controller: presented)
        }
        return controller
    }
    
    func presentAlertOnTopViewController(message: String) {
        DispatchQueue.main.async {
            guard let topViewController = UIApplication.shared.topViewController() else { return }
            let alertController = UIAlertController(title: "Message", message: message, preferredStyle: .alert)
            alertController.addAction(UIAlertAction(title: "OK", style: .default, handler: nil))
            alertController.modalPresentationStyle = .overFullScreen
            alertController.modalTransitionStyle = .crossDissolve
            topViewController.present(alertController, animated: true, completion: nil)
        }
    }
}
