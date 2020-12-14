//
//  VideoHelper.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-04-24.
//  Copyright © 2020 jx16. All rights reserved.
//

import AVFoundation
import Foundation

struct VideoHelper {
    
    static func generateThumbnail(videoUrl: URL) -> CGImage? {
        let asset = AVAsset(url: videoUrl)
        let generator = AVAssetImageGenerator.init(asset: asset)
        let cgImage = try? generator.copyCGImage(at: CMTimeMake(value: 0, timescale: 1), actualTime: nil)
        return cgImage
    }
    
    // https://stackoverflow.com/questions/29506411/ios-determine-number-of-frames-in-video
    static func getNumberOfFrames(videoUrl url: URL) -> Int {
        
        let asset = AVURLAsset(url: url, options: nil)
        do {
            let reader = try AVAssetReader(asset: asset)
            //AVAssetReader(asset: asset, error: nil)
            
            let videoTrack = asset.tracks(withMediaType: AVMediaType.video)[0]
            
            let readerOutput = AVAssetReaderTrackOutput(track: videoTrack, outputSettings: nil)
            reader.add(readerOutput)
            reader.startReading()
            
            var nFrames = 0
            
            while true {
                let sampleBuffer = readerOutput.copyNextSampleBuffer()
                if sampleBuffer == nil {
                    break
                }
                
                nFrames += 1
            }
            
            return nFrames
            
        } catch {
            print("Error: \(error)")
        }
        
        return 0
    }
}
