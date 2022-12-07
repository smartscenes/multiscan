import argparse
import os
import tempfile
import zlib
import logging
from enum import Enum

import cv2
import matplotlib.pyplot as plt
import numpy as np

from multiscan.utils import io
from multiprocessing import Pool

class ExportType(Enum):
    RAW = 0
    COLOR = 1
    GRAY = 2

class ParallelDepthDecode(object):
    def __init__(self, parameters):
        self.parameters = parameters
        self.tmp = self.parameters['tmp']
        self.tmp_confi = self.parameters['tmp_confi']
        self.depth_type = self.parameters['depth_type']
        self.height = self.parameters['height']
        self.width = self.parameters['width']
        self.frame_size = self.parameters['frame_size']
        self.confidence_filter = self.parameters['confidence_filter']
        self.output_confidence = self.parameters['output_confidence']
        self.output_depth = self.parameters['output_depth']
        self.depth_unit = self.parameters['depth_unit']
        self.level = self.parameters['level']
        self.depth_delta = self.parameters['depth_delta']
        self.pixel_size = self.parameters['pixel_size']
        self.depth_format = self.parameters['depth_format']
        self.export_type = self.parameters['export_type']
        self.confidence_color_levels = self.parameters['confidence_color_levels']

    def __call__(self, i):
        fp = np.memmap(self.tmp, dtype=self.depth_type, mode='r', shape=(self.height, self.width), 
                    offset=self.frame_size * i).copy()
        # depth delta difference filtering
        if self.depth_delta > 0 and i > 0:
            fp_last = np.memmap(self.tmp, dtype=self.depth_type, mode='r', shape=(self.height, self.width), 
                                offset=self.frame_size * (i - 1)).copy()
            delta = np.abs(fp_last - fp)
            fp[delta > self.depth_delta] = 0
        # filter with confidence levels
        if self.confidence_filter:
            fp_confi = np.memmap(self.tmp_confi, dtype='uint8', mode='r', shape=(self.height, self.width), 
                                offset=int(self.frame_size / self.pixel_size * i)).copy()
            fp[fp_confi < self.level] = 0

            # output color mapped confidence images
            if self.output_confidence:
                if self.export_type == ExportType.COLOR:
                    cm = plt.get_cmap('Reds', self.confidence_color_levels)
                    color = cm(fp_confi + 1)
                    color *= 255
                    color = color.astype('uint8')
                    color = cv2.cvtColor(color, cv2.COLOR_RGBA2BGRA)
                    cv2.imwrite(os.path.join(self.output_confidence, '{}.png'.format(i)), color)
                elif self.export_type == ExportType.RAW:
                    cv2.imwrite(os.path.join(self.output_confidence, '{}.png'.format(i)), fp_confi)

        # export depth images
        if self.export_type == ExportType.RAW:
            if self.depth_format == '.exr':
                fp = fp.astype('float32')
                if self.depth_unit == 'mm':
                    fp /= 1000.0
                cv2.imwrite(os.path.join(self.output_depth, '{}.exr'.format(i)), fp)
            elif self.depth_format == '.png':
                if self.depth_unit == 'm':
                    fp *= 1000
                fp = fp.astype('uint16')
                cv2.imwrite(os.path.join(self.output_depth, '{}.png'.format(i)), fp)
        
        elif self.export_type == ExportType.COLOR:
            clamp = 4.0
            if self.depth_unit == 'mm':
                clamp *= 1000.0
            cm = plt.get_cmap('jet')
            color = cm(fp.astype('float') / clamp)
            color *= 255
            color = color.astype('uint8')
            color = cv2.bitwise_and(color, color, mask=(fp!=0).astype('uint8'))
            color = cv2.cvtColor(color, cv2.COLOR_RGBA2BGR)
            cv2.imwrite(os.path.join(self.output_depth, '{}.png'.format(i)), color)
        elif self.export_type == ExportType.GRAY:  # write gray frames
            if self.depth_unit == 'm':
                fp *= 1000
            fp = fp.astype('uint16')
            gray = cv2.normalize(fp, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8UC1)
            cv2.imwrite(os.path.join(self.output_depth, '{}.png'.format(i)), gray)



def configure(args):
    if not io.file_exist(args.input, '.zlib'):
        logging.error(f'Input file {args.input} not exists')
        return False

    io.make_clean_folder(args.output)
    if not io.folder_exist(args.output):
        logging.error(f'Create result folder {args.output} failed')
        return False

    if args.output_confidence:
        io.make_clean_folder(args.output_confidence)

        if not io.folder_exist(args.output_confidence):
            logging.error(f'Create result folder {args.output} failed')
            return False

    if args.width < 1:
        logging.error(f'Width of frames must be positive integers')
        return False

    if args.height < 1:
        logging.error(f'Height of frames must be positive integers')
        return False

    return True


class DepthDecode:
    def __init__(self, input_depth, input_confidence=None):
        self.input_depth = input_depth
        self.input_confidence = input_confidence
        self.level = 2
        self.depth_delta = 0
        self.depth_unit = 'm'
        self.depth_format = '.exr'
        self.depth_size = 2 # pixel size in bytes
        self.step = 1
        self.width = 256
        self.height = 192

    @staticmethod
    def get_num_frames(num, width, height, tmpfile, pixel_size=2):
        file_size = os.stat(tmpfile.name).st_size
        frame_size = width * height * pixel_size
        if not num:
            num_frames = int(file_size / frame_size)
        else:
            num_frames = min(int(file_size / frame_size), num)

        return num_frames, frame_size

    @staticmethod
    def decompress(input, output):
        d = zlib.decompressobj(-zlib.MAX_WBITS)
        chuck_size = 4096 * 4
        tmp = tempfile.NamedTemporaryFile(
            prefix=os.path.basename(input), dir=output, delete=False)
        logging.debug('temp file name: ' + tmp.name)

        with open(input, 'rb') as f:
            buffer = f.read(chuck_size)
            while buffer:
                outstr = d.decompress(buffer)
                tmp.write(outstr)
                buffer = f.read(chuck_size)

            tmp.write(d.flush())
            tmp.close()

        return tmp

    def set_frame_params(self, width, height, depth_unit='m', pixel_size=2, depth_format='.exr'):
        self.width = width
        self.height = height
        self.depth_unit = depth_unit
        self.depth_format = depth_format
        self.pixel_size = pixel_size

    def set_filter_params(self, level, depth_delta):
        self.level = level
        self.depth_delta = depth_delta

    def decode(self, output_depth, output_confidence, step, export_type=ExportType.RAW, num=0, confidence_color_levels=4):
        tmp = self.decompress(self.input_depth, output_depth)
        confidence_filter = self.input_confidence and io.file_exist(self.input_confidence)
        if confidence_filter:
            tmp_confi = self.decompress(self.input_confidence, output_confidence)
        
        try:
            num_frames, frame_size = self.get_num_frames(num, self.width, self.height, tmp, self.pixel_size)
            out_num = int(num_frames / step)
            logging.info(f'{out_num} frames are being extracted')
            if self.depth_unit == 'm':
                depth_type = 'float16'
            elif self.depth_unit == 'mm':
                depth_type = 'uint16'
                self.depth_delta *= 1000
            else:
                logging.error(f"unsupported input depth unit {self.depth_unit}")
                raise ValueError

            pool = Pool(os.cpu_count())
            params = {}
            params['tmp'] = tmp.name
            params['tmp_confi'] = tmp_confi.name
            params['depth_type'] = depth_type
            params['height'] = self.height
            params['width'] = self.width
            params['frame_size'] = frame_size
            params['confidence_filter'] = confidence_filter
            params['output_confidence'] = output_confidence
            params['output_depth'] = output_depth
            params['depth_unit'] = self.depth_unit
            params['level'] = self.level
            params['depth_delta'] = self.depth_delta
            params['pixel_size'] = self.pixel_size
            params['depth_format'] = self.depth_format
            params['export_type'] = export_type
            params['confidence_color_levels'] = confidence_color_levels
            p_decode = ParallelDepthDecode(params)
            pool.map(p_decode, range(0, num_frames, step))

        except Exception as e:
            logging.error(e)
        
        os.unlink(tmp.name)
        if confidence_filter:
            os.unlink(tmp_confi.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Decode depth stream!')
    parser.add_argument('-in', '--input', dest='input', type=str, action='store', required=True,
                        help='Input depth stream zlib file')
    parser.add_argument('-in_confi', '--input_confidence', dest='input_confidence', type=str, action='store',
                        required=False,
                        help='Input confidence stream zlib file')
    parser.add_argument('-W', '--width', dest='width', type=int, default=256, action='store', required=False,
                        help='Width of each frame')
    parser.add_argument('-H', '--height', dest='height', type=int, default=192, action='store', required=False,
                        help='Height of each frame')
    parser.add_argument('-N', '--num', dest='num', type=int, default=0, action='store', required=False,
                        help='Totoal number of frames')
    parser.add_argument('-M', '--mode', dest='mode', type=int, default=0, action='store', required=False,
                        help='Mode of processing the zlib depth stream')
    parser.add_argument('-S', '--step', dest='step', type=int, default=1, action='store', required=False,
                        help='Step size of skipping poses')
    parser.add_argument('-TH', '--threshold', dest='threshold', type=float, default=0.05, action='store',
                        required=False,
                        help='Threshold for maximum depth delta difference')
    parser.add_argument('-F', '--filter', dest='filter', default=False, action='store_true', required=False,
                        help='Filter out points with large frame to frame delta')
    parser.add_argument('-L', '--level', dest='level', type=int, default=2, action='store', required=False,
                        help='Only consider points with confident greater than threshold')
    parser.add_argument('--pixel_size', dest='pixel_size', type=int, default=2, action='store', required=False,
                        help='Depth pixel size in bytes')
    parser.add_argument('--confi_color_range', dest='confi_color_range', type=int, default=4, action='store', required=False,
                        help='confidence colored images color range')
    parser.add_argument('-o', '--output', dest='output', type=str, action='store', required=True,
                        help='Output directory of decoding results')
    parser.add_argument('--unit', dest='unit', type=str, action='store', required=False,
                        default='m',
                        help='input depth unit (mm or m)')
    parser.add_argument('--format', dest='format', type=str, action='store', required=False,
                        default='.exr',
                        help='output depth format (.exr or .png)')
    parser.add_argument('-o_confi', '--output_confidence', dest='output_confidence', type=str, action='store',
                        required=False,
                        help='Output directory of confidence maps')

    args = parser.parse_args()

    if not configure(args):
        exit(0)
    if args.input_confidence:
        decoder = DepthDecode(args.input, args.input_confidence)
    else:
        decoder = DepthDecode(args.input)
    decoder.set_filter_params(args.level, args.threshold)
    decoder.set_frame_params(args.width, args.height, depth_unit=args.unit, pixel_size=args.pixel_size, depth_format=args.format)

    export_type = ExportType.RAW
    if args.mode == 1:
        export_type = ExportType.COLOR
    elif args.mode == 2:
        export_type = ExportType.GRAY
    
    decoder.decode(args.output, args.output_confidence, args.step, export_type=export_type, num=args.num,
                   confidence_color_levels=args.confi_color_range)
