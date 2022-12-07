import os
import json
import cv2
import logging
import time
from enum import Enum
import numpy as np
from decord import VideoReader
from decord import cpu

from multiscan.utils import io
from reconstruction.scripts.utils import decompress

log = logging.getLogger('reconstruct')

class File(Enum):
    META = 0
    COLOR = 1
    DEPTH = 2
    POSE = 3
    CONFIDENCE = 4


class Bridge:
    def __init__(self, config):
        self.config = config
        self.meta_file = None
        self.color_cap = None
        self.depth_file = None
        self.confidence_file = None
        self.pose_file = None

        self.meta = {}
        self.extrinsics = []
        self.intrinsics = []

    def open_all(self):
        if io.file_exist(self.config.input.color_stream):
            self._open_colorfile(self.config.input.color_stream)
        if io.file_exist(self.config.input.depth_stream):
            self._open_depthfile(self.config.input.depth_stream)
        if io.file_exist(self.config.input.confidence_stream):
            self._open_confidencefile(self.config.input.confidence_stream)
        if io.file_exist(self.config.input.metadata_file):
            self._open_metafile(self.config.input.metadata_file)
        if io.file_exist(self.config.input.trajectory_file):
            self._open_posefile(self.config.input.trajectory_file)

    def close_all(self):
        if self.color_cap:
            if self.config.alg_param.frames.use_opencv:
                self.color_cap.release()
            else:
                del self.color_cap
        if self.depth_file:
            os.unlink(self.depth_file.name)
        if self.confidence_file:
            os.unlink(self.confidence_file.name)
        if self.meta_file:
            self.meta_file.close()
        if self.pose_file:
            self.pose_file.close()

    def open_file(self, path, type=File.COLOR):
        options = {
            File.META: self._open_metafile,
            File.COLOR: self._open_colorfile,
            File.DEPTH: self._open_depthfile,
            File.POSE: self._open_posefile,
            File.CONFIDENCE: self._open_confidencefile
        }

        options[type](path)

    def _open_colorfile(self, path):
        if io.file_exist(path, '.mp4'):
            if self.config.alg_param.frames.use_opencv:
                self.color_cap = cv2.VideoCapture(path)
            else:
                self.color_cap = VideoReader(path, ctx=cpu(0))
        else:
            raise f'Color stream {path} does not exist'

    def _open_depthfile(self, path):
        filename = os.path.basename(path)
        if io.file_exist(path, '.zlib') and os.path.splitext(filename)[0].split('.')[1] == 'depth':
            self.depth_file = decompress(path)
        else:
            raise f'Depth stream {path} does not exist'

    def _open_confidencefile(self, path):
        filename = os.path.basename(path)
        if io.file_exist(path, '.zlib') and os.path.splitext(filename)[0].split('.')[1] == 'confidence':
            self.confidence_file = decompress(path)
        else:
            raise f'Confidence stream {path} does not exist'

    def _open_posefile(self, path):
        if io.file_exist(path, '.jsonl'):
            self.pose_file = open(path, 'r')
        else:
            raise f'Camera trajectory file {path} does not exist'

    def _open_metafile(self, path):
        if io.file_exist(path, '.json'):
            self.meta_file = open(path, 'r')
        else:
            raise f'Meta file {path} does not exist'

    def read_metadata(self):
        if self.meta_file != None:
            self.get_meta()

    def cap_colorframe(self, idx=0):
        if self.config.alg_param.frames.use_opencv:
            num_frames = self.color_cap.get(cv2.CAP_PROP_FRAME_COUNT)
        else:
            num_frames = len(self.color_cap)
        if num_frames != self.meta.get('num_frames', 0):
            logging.warning(f"color frames number not match in cv2 and meta, \
                     {num_frames} in .zlib, {self.meta.get('num_frames', 0)} in metadata")
            num_frames = min(self.meta.get('num_frames', 0), num_frames)

        self.meta['num_frames'] = num_frames

        if self.config.alg_param.frames.use_opencv:
            if idx >= 0 and idx < num_frames:
                self.color_cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                success, frame = self.color_cap.read()
            if success:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return frame
        else:
            if idx >= 0 and idx < num_frames:
                frame = self.color_cap[idx].asnumpy()
                return frame

    def filtered_depthframe(self, idx=0, level=2, delta_thresh=0.05):
        if self.meta['depth_format'] == 'mm':
            delta_thresh *= 1000

        fp = self.raw_depthframe(idx)
        if delta_thresh > 0:
            fp_last = self.raw_depthframe(idx - 1)
            delta = np.abs(fp_last - fp)
            fp[delta > delta_thresh] = 0

        if level >= 0 and self.confidence_file != None:
            fp_confidence = self.raw_confidenceframe(idx)
            fp[fp_confidence < level] = 0
            
        return np.array(fp).astype(np.float32)

    def raw_depthframe(self, idx=0):
        file_size = os.stat(self.depth_file.name).st_size
        frame_size = self.meta['depth_width'] * self.meta['depth_height'] * self.config.alg_param.frames.depth_pixel_size
        num_frames = int(file_size / frame_size)
        if num_frames != self.meta.get('num_frames', 0):
            logging.warning(f"depth frames number not match in .zlib and meta, \
                     {num_frames} in .zlib, {self.meta.get('num_frames', 0)} in metadata")
            num_frames = min(self.meta.get('num_frames', 0), num_frames)

        self.meta['num_frames'] = num_frames

        height = self.meta['depth_height']
        width = self.meta['depth_width']

        if self.meta['depth_format'] == 'm':
            depth_type = 'float16'
        elif self.meta['depth_format'] == 'mm':
            depth_type = 'uint16'

        if idx >= 0 and idx < num_frames:
            fp = np.memmap(self.depth_file.name, dtype=depth_type, mode='r', 
                shape=(height, width), offset=frame_size * idx).copy()
        elif idx <= 0:
            fp = np.memmap(self.depth_file.name, dtype=depth_type, mode='r', 
                shape=(height, width), offset=frame_size * 0).copy()
        else:
            fp = np.memmap(self.depth_file.name, dtype=depth_type, mode='r', 
                shape=(height, width), offset=frame_size * (num_frames - 1)).copy()
        return fp

    def raw_confidenceframe(self, idx=0):
        file_size = os.stat(self.confidence_file.name).st_size
        frame_size = self.meta['depth_width'] * self.meta['depth_height'] * self.config.alg_param.frames.confidence_pixel_size
        num_frames = int(file_size / frame_size)
        if num_frames != self.meta.get('num_frames', 0):
            logging.warning(f"confidence frames number not match in .zlib and meta, \
                     {num_frames} in .zlib, {self.meta.get('num_frames', 0)} in metadata")
            num_frames = min(self.meta.get('num_frames', 0), num_frames)

        self.meta['num_frames'] = num_frames

        height = self.meta['depth_height']
        width = self.meta['depth_width']
        if idx >= 0 and idx < num_frames:
            fp = np.memmap(self.confidence_file.name, dtype='uint8', mode='r', 
                shape=(height, width), offset=int(frame_size * idx)).copy()
            return fp

    def all_cameras(self):
        start_time = time.time()
        for line in self.pose_file:
            cam_info = json.loads(line)
            C= cam_info.get('transform', None) # ARKit pose (+x along long axis of device toward home button, +y upwards, +z away from device)
            assert C!= None
            C= np.asarray(C)
            C= C.reshape(4, 4).transpose()

            C= np.matmul(C, np.diag([1, -1, -1, 1])) # open3d camera pose (flip y and z)
            C= C / C[3][3]
            self.extrinsics.append(np.linalg.inv(C))

            scale_d2c_x = float(self.meta['depth_width']) / self.meta['color_width']
            scale_d2c_y = float(self.meta['depth_height']) / self.meta['color_height']

            K = cam_info.get('intrinsics', self.meta['intrinsic_data'])

            K = np.asarray(K)
            K = K.reshape(3, 3).transpose()
            scale = np.array([scale_d2c_x, scale_d2c_y, 1.0])
            K_depth = np.matmul(np.diag(scale), K)
            self.intrinsics.append(K_depth)
        
        log.info("--- %s seconds read camera extrinsics and intrinsics ---" % (time.time() - start_time))
        return self.extrinsics, self.intrinsics

    def get_camera_pose(self, idx=0):
        return self.extrinsics[idx]

    def get_camera_intrinsic(self, idx=0):
        return self.intrinsics[idx]

    def get_meta(self):
        meta = json.load(self.meta_file)

        self.meta['color_width'] = meta['streams'][0]['resolution'][1]
        self.meta['color_height'] = meta['streams'][0]['resolution'][0]
        self.meta['depth_width'] = meta['streams'][1]['resolution'][1]
        self.meta['depth_height'] = meta['streams'][1]['resolution'][0]
        self.meta['num_frames'] = min(
            meta['streams'][1]['number_of_frames'], meta['streams'][0]['number_of_frames'])
        self.meta['intrinsic_data'] = meta['streams'][0]['intrinsics']
        self.meta['depth_format'] = meta.get('depth_unit', 'm')
        logging.debug("depth unit", self.meta['depth_format'])
