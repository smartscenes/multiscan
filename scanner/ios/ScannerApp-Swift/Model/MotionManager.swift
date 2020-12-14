//
//  MotionManager.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-03-19.
//  Copyright © 2020 jx16. All rights reserved.
//

import CoreMotion

class MotionManager {
    
    private let motionManager = CMMotionManager()
    private let motionQueue = OperationQueue()
    
    private let motionDataOutputQueue = DispatchQueue(label: "motion data output queue")
    
//    private let bootTime: Double
    
    private var numberOfMeasurements: Int = 0
    private var isDebugMode: Bool = false
    
    private let imuUpdateFrequency:Int = 60
    
    private var rotationRateBinaryFileUrl: URL? = nil
    private var userAccelerationBinaryFileUrl: URL? = nil
    private var magneticFieldBinaryFileUrl: URL? = nil
    private var attitudeBinaryFileUrl: URL? = nil
    private var gravityBinaryFileUrl: URL? = nil
    
    private var rotationRateAsciiFileUrl: URL? = nil
    private var userAccelerationAsciiFileUrl: URL? = nil
    private var magneticFieldAsciiFileUrl: URL? = nil
    private var attitudeAsciiFileUrl: URL? = nil
    private var gravityAsciiFileUrl: URL? = nil
    
    private var rotationRateFileHandle: FileHandle? = nil
    private var userAccelerationFileHandle: FileHandle? = nil
    private var magneticFieldFileHandle: FileHandle? = nil
    private var attitudeFileHandle: FileHandle? = nil
    private var gravityFileHandle: FileHandle? = nil
    
    private var rotationRateAsciiFileHandle: FileHandle? = nil
    private var userAccelerationAsciiFileHandle: FileHandle? = nil
    private var magneticFieldAsciiFileHandle: FileHandle? = nil
    private var attitudeAsciiFileHandle: FileHandle? = nil
    private var gravityAsciiFileHandle: FileHandle? = nil
    
    init() {
        motionManager.deviceMotionUpdateInterval = 1.0 / Double(imuUpdateFrequency)
        motionQueue.maxConcurrentOperationCount = 1
        
        // we can use this if we want the real time instead of system up time
//        bootTime = Helper.bootTime()!
    }
    
    func startRecording(dataPathString: String, recordingId: String) {
        
        motionDataOutputQueue.async {
            
            self.numberOfMeasurements = 0
            self.isDebugMode = UserDefaults.debugFlag
            
            self.initFiles(dataPathString: dataPathString, recordingId: recordingId)
            
        }
        
        motionManager.startDeviceMotionUpdates(using: .xArbitraryCorrectedZVertical, to: self.motionQueue) { (data, error) in

            self.motionDataOutputQueue.async {
                
                if let validData = data {
                    
                    let motionData = MotionData(deviceMotion: validData)
//                    let motionData = MotionData(deviceMotion: validData, bootTime: self.bootTime)
                    
                    self.numberOfMeasurements += 1
                    self.writeData(motionData: motionData)

                } else {
                    print("there is some problem with motion data")
                }
            }
        }
        
    }
    
    func stopRecordingAndReturnStreamInfo() -> [ImuStreamInfo] {

        motionManager.stopDeviceMotionUpdates()

        motionDataOutputQueue.sync {
            closeFiles()
            addHeaders()
            resetFileUrls()
        }
        
        return generateStreamInfo()
    }
    
    private func initFiles(dataPathString: String, recordingId: String) {
        let rotationRatePath = (dataPathString as NSString).appendingPathComponent((recordingId as NSString).appendingPathExtension("rot")!)
        rotationRateBinaryFileUrl = URL(fileURLWithPath: rotationRatePath)
        FileManager.default.createFile(atPath: rotationRateBinaryFileUrl!.path, contents: nil, attributes: nil)

        let userAccelerationPath = (dataPathString as NSString).appendingPathComponent((recordingId as NSString).appendingPathExtension("acce")!)
        userAccelerationBinaryFileUrl = URL(fileURLWithPath: userAccelerationPath)
        FileManager.default.createFile(atPath: userAccelerationBinaryFileUrl!.path, contents: nil, attributes: nil)

        let magneticFieldPath = (dataPathString as NSString).appendingPathComponent((recordingId as NSString).appendingPathExtension("mag")!)
        magneticFieldBinaryFileUrl = URL(fileURLWithPath: magneticFieldPath)
        FileManager.default.createFile(atPath: magneticFieldBinaryFileUrl!.path, contents: nil, attributes: nil)

        let attitudePath = (dataPathString as NSString).appendingPathComponent((recordingId as NSString).appendingPathExtension("atti")!)
        attitudeBinaryFileUrl = URL(fileURLWithPath: attitudePath)
        FileManager.default.createFile(atPath: attitudeBinaryFileUrl!.path, contents: nil, attributes: nil)

        let gravityPath = (dataPathString as NSString).appendingPathComponent((recordingId as NSString).appendingPathExtension("grav")!)
        gravityBinaryFileUrl = URL(fileURLWithPath: gravityPath)
        FileManager.default.createFile(atPath: gravityBinaryFileUrl!.path, contents: nil, attributes: nil)

        rotationRateFileHandle = FileHandle(forUpdatingAtPath: rotationRateBinaryFileUrl!.path)
        userAccelerationFileHandle = FileHandle(forUpdatingAtPath: userAccelerationBinaryFileUrl!.path)
        magneticFieldFileHandle = FileHandle(forUpdatingAtPath: magneticFieldBinaryFileUrl!.path)
        attitudeFileHandle = FileHandle(forUpdatingAtPath: attitudeBinaryFileUrl!.path)
        gravityFileHandle = FileHandle(forUpdatingAtPath: gravityBinaryFileUrl!.path)
        
        if isDebugMode {
            rotationRateAsciiFileUrl = URL(fileURLWithPath: (rotationRatePath as NSString).appendingPathExtension("txt")!)
            FileManager.default.createFile(atPath: rotationRateAsciiFileUrl!.path, contents: nil, attributes: nil)
            
            userAccelerationAsciiFileUrl = URL(fileURLWithPath: (userAccelerationPath as NSString).appendingPathExtension("txt")!)
            FileManager.default.createFile(atPath: userAccelerationAsciiFileUrl!.path, contents: nil, attributes: nil)
            
            magneticFieldAsciiFileUrl = URL(fileURLWithPath: (magneticFieldPath as NSString).appendingPathExtension("txt")!)
            FileManager.default.createFile(atPath: magneticFieldAsciiFileUrl!.path, contents: nil, attributes: nil)
            
            attitudeAsciiFileUrl = URL(fileURLWithPath: (attitudePath as NSString).appendingPathExtension("txt")!)
            FileManager.default.createFile(atPath: attitudeAsciiFileUrl!.path, contents: nil, attributes: nil)
            
            gravityAsciiFileUrl = URL(fileURLWithPath: (gravityPath as NSString).appendingPathExtension("txt")!)
            FileManager.default.createFile(atPath: gravityAsciiFileUrl!.path, contents: nil, attributes: nil)
            
            rotationRateAsciiFileHandle = FileHandle(forUpdatingAtPath: rotationRateAsciiFileUrl!.path)
            userAccelerationAsciiFileHandle = FileHandle(forUpdatingAtPath: userAccelerationAsciiFileUrl!.path)
            magneticFieldAsciiFileHandle = FileHandle(forUpdatingAtPath: magneticFieldAsciiFileUrl!.path)
            attitudeAsciiFileHandle = FileHandle(forUpdatingAtPath: attitudeAsciiFileUrl!.path)
            gravityAsciiFileHandle = FileHandle(forUpdatingAtPath: gravityAsciiFileUrl!.path)
        
        }
    }
    
    private func closeFiles() {
        if rotationRateFileHandle != nil {
            rotationRateFileHandle!.closeFile()
            rotationRateFileHandle = nil
        }
        if userAccelerationFileHandle != nil {
            userAccelerationFileHandle!.closeFile()
            userAccelerationFileHandle = nil
        }
        if magneticFieldFileHandle != nil {
            magneticFieldFileHandle!.closeFile()
            magneticFieldFileHandle = nil
        }
        if attitudeFileHandle != nil {
            attitudeFileHandle!.closeFile()
            attitudeFileHandle = nil
        }
        if gravityFileHandle != nil {
            gravityFileHandle!.closeFile()
            gravityFileHandle = nil
        }
        
        if isDebugMode {
            
            if rotationRateAsciiFileHandle != nil {
                rotationRateAsciiFileHandle!.closeFile()
                rotationRateAsciiFileHandle = nil
            }
            if userAccelerationAsciiFileHandle != nil {
                userAccelerationAsciiFileHandle!.closeFile()
                userAccelerationAsciiFileHandle = nil
            }
            if magneticFieldAsciiFileHandle != nil {
                magneticFieldAsciiFileHandle!.closeFile()
                magneticFieldAsciiFileHandle = nil
            }
            if attitudeAsciiFileHandle != nil {
                attitudeAsciiFileHandle!.closeFile()
                attitudeAsciiFileHandle = nil
            }
            if gravityAsciiFileHandle != nil {
                gravityAsciiFileHandle!.closeFile()
                gravityAsciiFileHandle = nil
            }
        }
    }
    
    private func addHeaders() {
        addHeaderToFile(fileUrl: rotationRateBinaryFileUrl!, encoding: "bin", sensorType: "rot", numOfFrames: numberOfMeasurements)
        addHeaderToFile(fileUrl: userAccelerationBinaryFileUrl!, encoding: "bin", sensorType: "acce", numOfFrames: numberOfMeasurements)
        addHeaderToFile(fileUrl: magneticFieldBinaryFileUrl!, encoding: "bin", sensorType: "mag", numOfFrames: numberOfMeasurements)
        addHeaderToFile(fileUrl: attitudeBinaryFileUrl!, encoding: "bin", sensorType: "atti", numOfFrames: numberOfMeasurements)
        addHeaderToFile(fileUrl: gravityBinaryFileUrl!, encoding: "bin", sensorType: "gray", numOfFrames: numberOfMeasurements)
        
        if isDebugMode {
            addHeaderToFile(fileUrl: rotationRateAsciiFileUrl!, encoding: "ascii", sensorType: "rot", numOfFrames: numberOfMeasurements)
            addHeaderToFile(fileUrl: userAccelerationAsciiFileUrl!, encoding: "ascii", sensorType: "acce", numOfFrames: numberOfMeasurements)
            addHeaderToFile(fileUrl: magneticFieldAsciiFileUrl!, encoding: "ascii", sensorType: "mag", numOfFrames: numberOfMeasurements)
            addHeaderToFile(fileUrl: attitudeAsciiFileUrl!, encoding: "ascii", sensorType: "atti", numOfFrames: numberOfMeasurements)
            addHeaderToFile(fileUrl: gravityAsciiFileUrl!, encoding: "ascii", sensorType: "gray", numOfFrames: numberOfMeasurements)
        }
    }
    
    private func resetFileUrls() {
        rotationRateBinaryFileUrl = nil
        userAccelerationBinaryFileUrl = nil
        magneticFieldBinaryFileUrl = nil
        attitudeBinaryFileUrl = nil
        gravityBinaryFileUrl = nil
        
        rotationRateAsciiFileUrl = nil
        userAccelerationAsciiFileUrl = nil
        magneticFieldAsciiFileUrl = nil
        attitudeAsciiFileUrl = nil
        gravityAsciiFileUrl = nil
    }
    
    private func writeData(motionData: MotionData) {
        writeDataBinary(motionData: motionData)
        
        if self.isDebugMode {
            motionData.display()
            writeDataAscii(motionData: motionData)
        }
    }
    
    private func writeDataBinary(motionData: MotionData) {
        rotationRateFileHandle?.write(motionData.getRotationRateDataBinary())
        userAccelerationFileHandle?.write(motionData.getUserAccelerationDataBinary())
        magneticFieldFileHandle?.write(motionData.getMagneticFieldDataBinary())
        attitudeFileHandle?.write(motionData.getAttitudeDataBinary())
        gravityFileHandle?.write(motionData.getGravityDataBinary())
    }
    
    private func writeDataAscii(motionData: MotionData) {
        rotationRateAsciiFileHandle?.write(motionData.getRotationRateDataAscii())
        userAccelerationAsciiFileHandle?.write(motionData.getUserAccelerationDataAscii())
        magneticFieldAsciiFileHandle?.write(motionData.getMagneticFieldDataAscii())
        attitudeAsciiFileHandle?.write(motionData.getAttitudeDataAscii())
        gravityAsciiFileHandle?.write(motionData.getGravityDataAscii())
    }
    
    private func addHeaderToFile(fileUrl: URL, encoding: String, sensorType: String, numOfFrames: Int) {
        var header: String = "ply\n"

        switch encoding {
        case "bin":
            header += "format binary_little_endian 1.0\n"
        case "ascii":
            header += "format ascii 1.0\n"
        default:
            print("Invalid encoding")
        }
        
        header += "element \(sensorType) \(numOfFrames)\n"
        header += "comment\n"
        
        switch sensorType {
        case "rot", "acce", "mag", "grav":
            header += "property int64 timestamp\n"
            header += "property double x\n"
            header += "property double y\n"
            header += "property double z\n"
        case "atti":
            header += "property int64 timestamp\n"
            header += "property double roll\n"
            header += "property double pitch\n"
            header += "property double yaw\n"
        default:
            print("Invalid sensor type")
            return
        }
        
        header += "end_header\n"
        
        // base on
        // https://stackoverflow.com/questions/56441768/swift-how-to-append-text-line-to-top-of-file-txt
        do {
            let fileHandle = try FileHandle(forWritingTo: fileUrl)
            fileHandle.seek(toFileOffset: 0)
            let oldData = try Data(contentsOf: fileUrl)
            var data = header.data(using: .utf8)!
            data.append(oldData)
            fileHandle.write(data)
            fileHandle.closeFile()
        } catch {
            print("Error writing to file \(error)")
        }
    }
    
    private func generateStreamInfo() -> [ImuStreamInfo] {
        let rotationRateStreamInfo = ImuStreamInfo(id: "rot_1", type: "rot", encoding: "bin", frequency: imuUpdateFrequency, numberOfFrames: numberOfMeasurements, fileExtension: "rot")
        let userAccelerationStreamInfo = ImuStreamInfo(id: "acce_1", type: "acce", encoding: "bin", frequency: imuUpdateFrequency, numberOfFrames: numberOfMeasurements, fileExtension: "acce")
        let magneticFieldStreamInfo = ImuStreamInfo(id: "mag_1", type: "mag", encoding: "bin", frequency: imuUpdateFrequency, numberOfFrames: numberOfMeasurements, fileExtension: "mag")
        let attitudeStreamInfo = ImuStreamInfo(id: "atti_1", type: "atti", encoding: "bin", frequency: imuUpdateFrequency, numberOfFrames: numberOfMeasurements, fileExtension: "atti")
        let gravityStreamInfo = ImuStreamInfo(id: "grav_1", type: "gray", encoding: "bin", frequency: imuUpdateFrequency, numberOfFrames: numberOfMeasurements, fileExtension: "gray")

        return [rotationRateStreamInfo, userAccelerationStreamInfo, magneticFieldStreamInfo, attitudeStreamInfo, gravityStreamInfo]
    }
}
