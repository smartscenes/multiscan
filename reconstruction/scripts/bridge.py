import os
import cv2
import numpy as np
import zlib
import tempfile
from enum import Enum
import json
import functions.utils as utils
import open3d as o3d

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
        self.poses = []
        self.instrinsics = []

    def open_all(self):
        if utils.file_exist(self.config.setting.io.color_path):
            self._open_colorfile(self.config.setting.io.color_path)
        if utils.file_exist(self.config.setting.io.depth_path):
            self._open_depthfile(self.config.setting.io.depth_path)
        if utils.file_exist(self.config.setting.io.confidence_path):
            self._open_confidencefile(self.config.setting.io.confidence_path)
        if utils.file_exist(self.config.setting.io.meta_path):
            self._open_metafile(self.config.setting.io.meta_path)
        if utils.file_exist(self.config.setting.io.trajectory_path):
            self._open_posefile(self.config.setting.io.trajectory_path)

    def close_all(self):
        if self.color_cap:
            self.color_cap.release()
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
            File.POSE: self._open_confidencefile,
            File.CONFIDENCE: self._open_confidencefile
        }

        options[type](path)

    def _open_colorfile(self, path):
        if utils.file_exist(path, '.mp4'):
            self.color_cap = cv2.VideoCapture(path)
        else:
            raise f'Color stream {path} does not exist'
    
    def _open_depthfile(self, path):
        filename = os.path.basename(path)
        if utils.file_exist(path, '.zlib') and os.path.splitext(filename)[0].split('.')[1] == 'depth':
            self.depth_file = utils.decompress(path)
        else:
            raise f'Depth stream {path} does not exist'

    def _open_confidencefile(self, path):
        filename = os.path.basename(path)
        if utils.file_exist(path, '.zlib') and os.path.splitext(filename)[0].split('.')[1] == 'confidence':
            self.confidence_file = utils.decompress(path)
        else:
            raise f'Confidence stream {path} does not exist'

    def _open_posefile(self, path):
        if utils.file_exist(path, '.jsonl'):
            self.pose_file = open(path, 'r')
        else:
            raise f'Camera trajectory file {path} does not exist'

    def _open_metafile(self, path):
        if utils.file_exist(path, '.json'):
            self.meta_file = open(path, 'r')
        else:
            raise f'Meta file {path} does not exist'

    def preprocess(self):
        if self.meta_file != None:
            self.get_meta()
        if self.pose_file != None:
            self.all_cameras()

    def cap_colorframe(self, idx=0):
        num_frames = self.color_cap.get(cv2.CAP_PROP_FRAME_COUNT)
        assert num_frames == self.meta.get('num_frames', 0), 'color frames number not match in cv2 and meta'
        if idx >= 0 and idx < num_frames:
            self.color_cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            success, frame = self.color_cap.read()
        if success:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame
    
    def filtered_depthframe(self, idx=0, level=1, delta_thresh=0.05):
        fp = self.raw_depthframe(idx)
        if delta_thresh > 0:
            fp_last = self.raw_depthframe(idx-1)
            delta = np.abs(fp_last - fp)
            fp[delta>delta_thresh]=0
        
        if level >= 0 and self.confidence_file != None:
            fp_confidence = self.raw_confidenceframe(idx)
            fp[fp_confidence<=level]=0
        
        fp *= 1000
        fp = fp.astype('uint16')
        return fp

    def raw_depthframe(self, idx=0):
        file_size = os.stat(self.depth_file.name).st_size
        frame_size = self.meta['depth_width']*self.meta['depth_height']*2
        num_frames = int(file_size/frame_size)
        assert num_frames == self.meta.get('num_frames', 0), 'depth frames number not match in .zlib and meta'

        height = self.meta['depth_height']
        width = self.meta['depth_width']
        if idx >= 0 and idx < num_frames:
            fp = np.memmap(self.depth_file.name, dtype='float16', mode='r', shape=(height, width), offset=frame_size*idx).copy()
        elif idx <= 0:
            fp = np.memmap(self.depth_file.name, dtype='float16', mode='r', shape=(height, width), offset=frame_size*0).copy()
        else:
            fp = np.memmap(self.depth_file.name, dtype='float16', mode='r', shape=(height, width), offset=frame_size*(num_frames-1)).copy()
        return fp
            
        
    def raw_confidenceframe(self, idx=0):
        file_size = os.stat(self.confidence_file.name).st_size
        frame_size = self.meta['depth_width']*self.meta['depth_height']
        num_frames = int(file_size/frame_size)
        assert num_frames == self.meta.get('num_frames', 0), 'confidence frames number not match in .zlib and meta'

        height = self.meta['depth_height']
        width = self.meta['depth_width']
        if idx >= 0 and idx < num_frames:
            fp = np.memmap(self.confidence_file.name, dtype='uint8', mode='r', shape=(height, width), offset=int(frame_size*idx)).copy()
            return fp

    def all_cameras(self):
        for line in self.pose_file:
            cam_info = json.loads(line)
            trans = cam_info.get('transform', None)
            assert trans != None
            trans = np.asarray(trans)
            trans = trans.reshape(4, 4).transpose()

            trans = np.matmul(trans, np.diag([1, -1, -1, 1]))
            trans = trans/trans[3][3]
            self.poses.append(trans)

            scale_x = float(self.meta['depth_width'])/self.meta['color_width']
            scale_y = float(self.meta['depth_height'])/self.meta['color_height']
            
            intrinsic = cam_info.get('intrinsics', self.meta['intrinsic_data'])

            intrinsic = np.asarray(intrinsic).astype(np.float32)
            intrinsic = intrinsic.reshape(3, 3).transpose()
            scale = np.array([scale_x, scale_y, 1.0])
            intrinsic = np.matmul(np.diag(scale), intrinsic)
            intrinsic = intrinsic.flatten('F').tolist()

            intrinsic = o3d.camera.PinholeCameraIntrinsic(self.meta['depth_width'], self.meta['depth_height'],
                intrinsic[0], intrinsic[4], intrinsic[6], intrinsic[7])
            self.instrinsics.append(intrinsic)
            
        
        return self.poses, self.instrinsics

    def get_camera_pose(self, idx=0):
        return self.poses[idx]

    def get_camera_intrinsic(self, idx=0):
        return self.instrinsics[idx]

    def get_meta(self):
        meta = json.load(self.meta_file)
        
        self.meta['color_width'] = meta['streams'][0]['resolution'][1]
        self.meta['color_height'] = meta['streams'][0]['resolution'][0]
        self.meta['depth_width'] = meta['streams'][1]['resolution'][1]
        self.meta['depth_height'] = meta['streams'][1]['resolution'][0]
        self.meta['num_frames'] = min(meta['streams'][1]['number_of_frames'], meta['streams'][0]['number_of_frames'])
        self.meta['intrinsic_data'] = meta['streams'][0]['intrinsics']

