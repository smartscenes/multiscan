//
//  RecordingManager.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-11-17.
//  Copyright © 2020 jx16. All rights reserved.
//

import Foundation

protocol RecordingManager {
    var isRecording: Bool { get }
    
    func getSession() -> NSObject
    
    func startRecording(username: String, sceneDescription: String, sceneType: String)
    func stopRecording()
}
