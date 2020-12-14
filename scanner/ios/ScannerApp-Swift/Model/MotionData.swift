//
//  MotionData.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2019-12-28.
//  Copyright © 2019 jx16. All rights reserved.
//

import CoreMotion
import Foundation

class MotionData {
    
    private var timestamp: Int64
    private var rotX: Double
    private var rotY: Double
    private var rotZ: Double
    private var accX: Double
    private var accY: Double
    private var accZ: Double
    private var magX: Double
    private var magY: Double
    private var magZ: Double
    private var roll: Double
    private var pitch: Double
    private var yaw: Double
    private var gravX: Double
    private var gravY: Double
    private var gravZ: Double

    init(deviceMotion data: CMDeviceMotion) {
        
        self.timestamp = Int64(data.timestamp * 1_000_000_000.0)
        
        self.rotX = data.rotationRate.x
        self.rotY = data.rotationRate.y
        self.rotZ = data.rotationRate.z
        
        self.accX = data.userAcceleration.x
        self.accY = data.userAcceleration.y
        self.accZ = data.userAcceleration.z
        
        self.magX = data.magneticField.field.x
        self.magY = data.magneticField.field.y
        self.magZ = data.magneticField.field.z
        
        self.roll = data.attitude.roll
        self.pitch = data.attitude.pitch
        self.yaw = data.attitude.yaw
        
        self.gravX = data.gravity.x
        self.gravY = data.gravity.y
        self.gravZ = data.gravity.z
    }
    
    init(deviceMotion data: CMDeviceMotion, bootTime: Double) {
        
        let actualTime = data.timestamp + bootTime
        
        self.timestamp = Int64(actualTime * 1_000_000_000.0)
        
        self.rotX = data.rotationRate.x
        self.rotY = data.rotationRate.y
        self.rotZ = data.rotationRate.z
        
        self.accX = data.userAcceleration.x
        self.accY = data.userAcceleration.y
        self.accZ = data.userAcceleration.z
        
        self.magX = data.magneticField.field.x
        self.magY = data.magneticField.field.y
        self.magZ = data.magneticField.field.z
        
        self.roll = data.attitude.roll
        self.pitch = data.attitude.pitch
        self.yaw = data.attitude.yaw
        
        self.gravX = data.gravity.x
        self.gravY = data.gravity.y
        self.gravZ = data.gravity.z
    }
    
    func display() {
        print("System Uptime: \(self.timestamp)")
        print("Rotation: \(self.rotX), \(self.rotY), \(self.rotZ)")
        print("Acceleration: \(self.accX), \(self.accY), \(self.accZ)")
        print("Magnetic Field: \(self.magX), \(self.magY), \(self.magZ)")
        print("Roll: \(self.roll)")
        print("Pitch: \(self.pitch)")
        print("Yaw: \(self.yaw)")
        print("Gravity: \(self.gravX), \(self.gravY), \(self.gravZ)")
    }
    
    func getRotationRateDataBinary() -> Data {
        let dataPointer = UnsafeMutableRawPointer.allocate(byteCount: 32, alignment: 1)
        dataPointer.storeBytes(of: timestamp.littleEndian, toByteOffset: 0, as: Int64.self)
        dataPointer.storeBytes(of: rotX.bitPattern.littleEndian, toByteOffset: 8, as: UInt64.self)
        dataPointer.storeBytes(of: rotY.bitPattern.littleEndian, toByteOffset: 16, as: UInt64.self)
        dataPointer.storeBytes(of: rotZ.bitPattern.littleEndian, toByteOffset: 24, as: UInt64.self)
        return Data(bytes: dataPointer, count: 32)
    }
    
    func getUserAccelerationDataBinary() -> Data {
        let dataPointer = UnsafeMutableRawPointer.allocate(byteCount: 32, alignment: 1)
        dataPointer.storeBytes(of: timestamp.littleEndian, toByteOffset: 0, as: Int64.self)
        dataPointer.storeBytes(of: accX.bitPattern.littleEndian, toByteOffset: 8, as: UInt64.self)
        dataPointer.storeBytes(of: accY.bitPattern.littleEndian, toByteOffset: 16, as: UInt64.self)
        dataPointer.storeBytes(of: accZ.bitPattern.littleEndian, toByteOffset: 24, as: UInt64.self)
        return Data(bytes: dataPointer, count: 32)
    }
    
    func getMagneticFieldDataBinary() -> Data {
        let dataPointer = UnsafeMutableRawPointer.allocate(byteCount: 32, alignment: 1)
        dataPointer.storeBytes(of: timestamp.littleEndian, toByteOffset: 0, as: Int64.self)
        dataPointer.storeBytes(of: magX.bitPattern.littleEndian, toByteOffset: 8, as: UInt64.self)
        dataPointer.storeBytes(of: magY.bitPattern.littleEndian, toByteOffset: 16, as: UInt64.self)
        dataPointer.storeBytes(of: magZ.bitPattern.littleEndian, toByteOffset: 24, as: UInt64.self)
        return Data(bytes: dataPointer, count: 32)
    }
    
    func getAttitudeDataBinary() -> Data {
        let dataPointer = UnsafeMutableRawPointer.allocate(byteCount: 32, alignment: 1)
        dataPointer.storeBytes(of: timestamp.littleEndian, toByteOffset: 0, as: Int64.self)
        dataPointer.storeBytes(of: roll.bitPattern.littleEndian, toByteOffset: 8, as: UInt64.self)
        dataPointer.storeBytes(of: pitch.bitPattern.littleEndian, toByteOffset: 16, as: UInt64.self)
        dataPointer.storeBytes(of: yaw.bitPattern.littleEndian, toByteOffset: 24, as: UInt64.self)
        return Data(bytes: dataPointer, count: 32)
    }
    
    func getGravityDataBinary() -> Data {
        let dataPointer = UnsafeMutableRawPointer.allocate(byteCount: 32, alignment: 1)
        dataPointer.storeBytes(of: timestamp.littleEndian, toByteOffset: 0, as: Int64.self)
        dataPointer.storeBytes(of: gravX.bitPattern.littleEndian, toByteOffset: 8, as: UInt64.self)
        dataPointer.storeBytes(of: gravY.bitPattern.littleEndian, toByteOffset: 16, as: UInt64.self)
        dataPointer.storeBytes(of: gravZ.bitPattern.littleEndian, toByteOffset: 24, as: UInt64.self)
        return Data(bytes: dataPointer, count: 32)
    }
    
    func getRotationRateDataAscii() -> Data {
        let dataString = "\(timestamp) \(rotX) \(rotY) \(rotZ)\n"
        return dataString.data(using: .ascii)!
    }
    
    func getUserAccelerationDataAscii() -> Data {
        let dataString = "\(timestamp) \(accX) \(accY) \(accZ)\n"
        return dataString.data(using: .ascii)!
    }
    
    func getMagneticFieldDataAscii() -> Data {
        let dataString = "\(timestamp) \(magX) \(magY) \(magZ)\n"
        return dataString.data(using: .ascii)!
    }
    
    func getAttitudeDataAscii() -> Data {
        let dataString = "\(timestamp) \(roll) \(pitch) \(yaw)\n"
        return dataString.data(using: .ascii)!
    }
    
    func getGravityDataAscii() -> Data {
        let dataString = "\(timestamp) \(gravX) \(gravY) \(gravZ)\n"
        return dataString.data(using: .ascii)!
    }
    
}
