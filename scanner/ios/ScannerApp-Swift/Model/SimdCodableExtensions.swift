//
//  SimdCodableExtensions.swift
//  ScannerApp-Swift
//
//  Created by Zheren Xiao on 2020-11-23.
//  Copyright © 2020 jx16. All rights reserved.
//

import simd

extension simd_float3x3: Codable {
    var arrayRepresentation: [Float] {
        return [self.columns.0.x, self.columns.0.y, self.columns.0.z,
                self.columns.1.x, self.columns.1.y, self.columns.1.z,
                self.columns.2.x, self.columns.2.y, self.columns.2.z]
    }
    
    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        let array = try container.decode([Float].self)
        self.init([SIMD3<Float>(array[0], array[1], array[2]),
                   SIMD3<Float>(array[3], array[4], array[5]),
                   SIMD3<Float>(array[6], array[7], array[8])])
    }
    
    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode(self.arrayRepresentation)
    }
}

extension simd_float4x4: Codable {
    var arrayRepresentation: [Float] {
        return [self.columns.0.x, self.columns.0.y, self.columns.0.z, self.columns.0.w,
                self.columns.1.x, self.columns.1.y, self.columns.1.z, self.columns.1.w,
                self.columns.2.x, self.columns.2.y, self.columns.2.z, self.columns.2.w,
                self.columns.3.x, self.columns.3.y, self.columns.3.z, self.columns.3.w]
    }
    
    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        let array = try container.decode([Float].self)
        self.init([SIMD4<Float>(array[0], array[1], array[2], array[3]),
                   SIMD4<Float>(array[4], array[5], array[6], array[7]),
                   SIMD4<Float>(array[8], array[9], array[10], array[11]),
                   SIMD4<Float>(array[12], array[13], array[14], array[15])])
    }
    
    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        try container.encode(self.arrayRepresentation)
    }
}
