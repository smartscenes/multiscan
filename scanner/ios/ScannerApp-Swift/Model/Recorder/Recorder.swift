//
//  Recorder.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-11-26.
//  Copyright © 2020 jx16. All rights reserved.
//

import CoreMedia

protocol Recorder {
    associatedtype T
    
    func prepareForRecording(dirPath: String, filename: String, fileExtension: String)
    func update(_: T, timestamp: CMTime?)
    func finishRecording()
}
