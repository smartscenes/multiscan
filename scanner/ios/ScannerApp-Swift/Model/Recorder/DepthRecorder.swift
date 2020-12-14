//
//  DepthRecorder.swift
//  LiDARDepth
//
//  Created by Zheren Xiao on 2020-09-21.
//  Copyright © 2020 jx16. All rights reserved.
//

import Accelerate.vImage
import Compression
import CoreMedia
import CoreVideo
import Foundation

class DepthRecorder: Recorder {
    typealias T = CVPixelBuffer
    
    private let depthQueue = DispatchQueue(label: "depth queue")
    
    private var fileHandle: FileHandle? = nil
    private var fileUrl: URL? = nil
    private var compressedFileUrl: URL? = nil
    
    private var count: Int32 = 0
    
    func prepareForRecording(dirPath: String, filename: String, fileExtension: String = "depth") {
        
        depthQueue.async {
            
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
        
        depthQueue.async {
            
            print("Saving frame \(self.count) ...")
            
//            self.writePixelBufferToFile(buffer: buffer)
//            self.convertF32DepthMapToF16PixelByPixelAndWriteToFile(buffer: buffer)
            self.convertF32DepthMapToF16AndWriteToFile(f32CVPixelBuffer: buffer)
            
            self.count += 1
        }
        
    }
    
    func finishRecording() {
        
        depthQueue.async {
            if self.fileHandle != nil {
                self.fileHandle!.closeFile()
                self.fileHandle = nil
            }
            
            print("\(self.count) frames saved.")
            
            self.compressFile()
            self.removeUncompressedFile()
            
        }
        
    }
    
    func displayBufferInfo(buffer: CVPixelBuffer) {
        
        depthQueue.async {
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
        self.fileHandle?.write(data)

        CVPixelBufferUnlockBaseAddress(buffer, .readOnly)
    }
    
    @available(iOS 14.0, *)
    private func convertF32DepthMapToF16PixelByPixelAndWriteToFile(buffer: CVPixelBuffer) {
        CVPixelBufferLockBaseAddress(buffer, .readOnly)
        
        let baseAddress: UnsafeMutableRawPointer = CVPixelBufferGetBaseAddress(buffer)!
        
        let height = CVPixelBufferGetHeight(buffer)
        let width = CVPixelBufferGetWidth(buffer)
        let numPixel = height * width
        
//        var data = Data()
        let f16Pointer = UnsafeMutableRawPointer.allocate(byteCount: numPixel*2, alignment: 1)
        
        for i in 0..<numPixel {
            let f32 = baseAddress.load(fromByteOffset: i*4, as: Float32.self)
//            print("32-bit depth[\(i)] in meter: \(f32)")
//            var f16 = Float16(f32)
//            print("16-bit depth[\(i)] in meter: \(f16)")
//            self.fileHandle?.write(Data(bytes: &f16, count: 2))
            
//            data.append(Data(bytes: &f16, count: 2))
            f16Pointer.storeBytes(of: Float16(f32), toByteOffset: i*2, as: Float16.self)
            
        }
        
//        self.fileHandle?.write(data)
        self.fileHandle?.write(Data(bytes: f16Pointer, count: numPixel*2))
        
        f16Pointer.deallocate()
        
        CVPixelBufferUnlockBaseAddress(buffer, .readOnly)
    }
    
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
        
        self.fileHandle?.write(Data(bytesNoCopy: f16vImageBuffer.data, count: numPixel * 2, deallocator: .none))
        
        CVPixelBufferUnlockBaseAddress(f32CVPixelBuffer, .readOnly)
        
    }
    
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
