/**
* Copyright (c) 2016 Razeware LLC
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in
* all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
* THE SOFTWARE.
*/

import Foundation
import Compression

public enum CompressionAlgorithm {
	case lz4   // speed is critical
	case lz4a  // space is critical
	case zlib  // reasonable speed and space
	case lzfse // better speed and space
}

public enum CompressionFlag {
	case COMPRESSING
	case COMPRESSION_END
}

public enum CompressionOperation {
	case compression, decompression
}

/// This is a sample compressor class from Apple, and its no longer used
class Compressor {
	private let _stream_ptr: UnsafeMutablePointer<compression_stream>
	private let _algorithm: compression_algorithm
	private let _operation: compression_stream_operation
	private var _stream: compression_stream
	private var _status: compression_status
	private var _src_size: Int = 0
	private var _src_ptr: UnsafeMutableRawPointer?
	private let _dst_size: Int = 1024*32*4
	private let _dst_ptr: UnsafeMutablePointer<UInt8>?
	
	init(operation: CompressionOperation, algorithm: CompressionAlgorithm) {
		_stream_ptr = UnsafeMutablePointer<compression_stream>
			.allocate(capacity: 1)

		// set the algorithm
		switch algorithm {
		case .lz4:   _algorithm = COMPRESSION_LZ4
		case .lz4a:  _algorithm = COMPRESSION_LZMA
		case .zlib:  _algorithm = COMPRESSION_ZLIB
		case .lzfse: _algorithm = COMPRESSION_LZFSE
		}
		
		// set the operation
		switch operation {
		case .compression:
			_operation = COMPRESSION_STREAM_ENCODE
		case .decompression:
			_operation = COMPRESSION_STREAM_DECODE
		}
		
		_stream = _stream_ptr.pointee
		_status = compression_stream_init(&_stream, _operation, _algorithm)
		guard _status != COMPRESSION_STATUS_ERROR else {
			fatalError("Unable to initialize the compression stream.")
		}
		
		_dst_ptr = UnsafeMutablePointer<UInt8>.allocate(capacity: _dst_size)
	}
	
	deinit {
		_stream_ptr.deallocate()
		compression_stream_destroy(&_stream)
		_dst_ptr?.deallocate()
	}
	
	public func perform(input: Data) -> Data? {
		return performImpl(input: input, flag: Int32(0), buffer_size: input.count)
	}
	
	public func performImpl(input: Data, flag: Int32, buffer_size: Int) -> Data? {
		var iter = 0
		var output = Data()
		
		return input.withUnsafeBytes { (srcPointer: UnsafePointer<UInt8>) in
			_stream.src_ptr = srcPointer
			_stream.src_size = input.count
			_stream.dst_ptr = _dst_ptr!
			_stream.dst_size = _dst_size
			
			var last_size: Int = 0
			while true {
				last_size = min(_stream.src_size, _dst_size)
				_stream.src_size = last_size
				if _stream.src_size == 0 {
					if flag == 0{
						return output
					}
					
					if _status == COMPRESSION_STATUS_END {
						return output
					}
				}
				
				// process the stream
				_status = compression_stream_process(&_stream, flag)
				print(_status)
				
				// collect bytes from the stream and reset
				switch _status {
				
				case COMPRESSION_STATUS_OK,
					 COMPRESSION_STATUS_END:
					output.append(_dst_ptr!, count: _dst_size - _stream.dst_size)
					_stream.dst_ptr = _dst_ptr!
					_stream.dst_size = _dst_size
				case COMPRESSION_STATUS_ERROR:
					return nil
					
				default:
					fatalError()
				}
				
				iter += 1
				
				_stream.src_ptr = srcPointer.advanced(by: last_size)
				_stream.src_size = input.count - iter*_dst_size
				_stream.src_size = max(0, _stream.src_size)
			}
			return output
		}
	}
		
	public func finish() -> Data? {
		return performImpl(input: Data(), flag: Int32(COMPRESSION_STREAM_FINALIZE.rawValue), buffer_size: 1024*32)
	}
}
