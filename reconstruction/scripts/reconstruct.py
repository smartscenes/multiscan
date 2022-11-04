import os
import sys
import time
import logging

import open3d as o3d
import numpy as np
from progress.bar import Bar

from reconstruction.scripts.utils import align_color2depth
from reconstruction.scripts.base import ReconBase

from multiscan.meshproc import TriMesh
from multiscan.utils import io

log = logging.getLogger('reconstruct')

from enum import Enum
class VoxelType(Enum):
    Float32 = o3d.core.Dtype.Float32
    Float64 = o3d.core.Dtype.Float64
    Int8 = o3d.core.Dtype.Int8
    Int16 = o3d.core.Dtype.Int16
    Int32 = o3d.core.Dtype.Int32
    Int64 = o3d.core.Dtype.Int64
    UInt8 = o3d.core.Dtype.UInt8
    UInt16 = o3d.core.Dtype.UInt16
    UInt32 = o3d.core.Dtype.UInt32
    UInt64 = o3d.core.Dtype.UInt64

class VolumeType(Enum):
    TSDFVoxelGrid = 0
    ScalableTSDFVolume = 1


class Reconstruct(ReconBase):
    """reconstruction class
    input a sequence of RGBD images or uncompressed streams, output a point cloud or a mesh
    """

    def __init__(self, config, bridge=None):
        super().__init__(config, bridge)
        self._extrinsics = []
        self._intrinsics = []
        self.device_name = f'{self.config.settings.device_type}:{self.config.settings.device_id}'
        self.device = o3d.core.Device(self.device_name)
        self.to_gpu = True if self.config.settings.device_type == 'gpu' else False
        # reconstruct from decoded images with multiway registration
        if os.path.isdir(self.config.input.depth_stream) and self.bridge is None:
            self._frame_files = self.read_images()
            self._num_frames = self._frame_files.num
            self._intrinsic = self.read_intrinsic()
            self._intrinsics.append(self._intrinsic)
            self._frame_i_abs = []
        # reconstruct from decoded images and known camera poses
        elif os.path.isdir(self.config.input.depth_stream) and self.bridge is not None:
            self._frame_files = self.read_images()
            self._num_frames = self._frame_files.num
            self._frame_i_abs = list(range(0, self._num_frames))
        # reconstruct from compressed streams and known camera poses
        elif os.path.isfile(self.config.input.depth_stream):
            self._num_frames = bridge.meta['num_frames']
            self._frame_i_abs = list(range(0, self._num_frames))
        
        self._skip_step = 1
        if self.config.alg_param.frames.step > 0:
            self._skip_step = self.config.alg_param.frames.step

        if self.config.settings.debug:
            log.setLevel(logging.DEBUG)

    def export(self, volume):
        """export reconstruction results

        :param volume: integration volume
        :return: None
        """
        cfg_output = self.config.output
        io.ensure_dir_exists(self.save_folder())
        if self.config.settings.extract_mesh:
            mesh_path = os.path.join(self.save_folder(), cfg_output.mesh_filename)
            log.info("Extract triangle mesh")
            if VolumeType[self.config.alg_param.volume_type] == VolumeType.TSDFVoxelGrid:
                mesh = volume.cpu().extract_surface_mesh(weight_threshold=self.config.alg_param.extract.weight_threshold).to_legacy_triangle_mesh()
            else:
                mesh = volume.extract_triangle_mesh()
            unaligned_mesh_filename = os.path.splitext(mesh_path)[0] + '_unaligned.ply'
            success = o3d.io.write_triangle_mesh(
                unaligned_mesh_filename, mesh, write_vertex_normals=True)
            TriMesh.cleanup_mesh(unaligned_mesh_filename)
            log.info("Result saved to : {}".format(unaligned_mesh_filename))

            if success and io.is_non_zero_file(unaligned_mesh_filename):
                # mesh decimation with instant meshes
                decimated_mesh_path = os.path.join(self.save_folder(), cfg_output.decimated_mesh_filename)
                unaligned_decimated_mesh_path = os.path.splitext(decimated_mesh_path)[0] + '_unaligned.ply'
                log.info(f'Start mesh decimation')
                cfg_decimation = self.config.alg_param.decimation
                set_dominant = '--dominant' if cfg_decimation.dominant else ''
                ret = io.call(
                    ['./' + self.config.settings.instant_meshes_bin, unaligned_mesh_filename, 
                    '-c', str(cfg_decimation.crease), set_dominant,
                    '-r', str(cfg_decimation.rosy), '-p', str(cfg_decimation.posy), 
                    '-v', str(int(np.asarray(mesh.vertices).shape[0] / cfg_decimation.degree)),
                    '-o', unaligned_decimated_mesh_path], log, self.config.settings.instant_meshes_path)
                if not ret:
                    # mesh clean up and coordinate alignment
                    TriMesh.cleanup_mesh(unaligned_decimated_mesh_path)
                    decimated_mesh = TriMesh(unaligned_decimated_mesh_path)
                    transform_mat = decimated_mesh.align_mesh(
                        os.path.join(self.save_folder(), cfg_output.mesh_alignment_filename))
                    o3d.io.write_triangle_mesh(
                        decimated_mesh_path, decimated_mesh.o3d_mesh, write_vertex_normals=True)
                    log.info("Decimated mesh saved to : {}".format(decimated_mesh_path))

                    raw_mesh = TriMesh(unaligned_mesh_filename)
                    raw_mesh.o3d_mesh.transform(np.linalg.inv(transform_mat))
                    o3d.io.write_triangle_mesh(
                        mesh_path, raw_mesh.o3d_mesh, write_vertex_normals=True)
                    log.info("Undecimated mesh saved to : {}".format(mesh_path))

        if self.config.settings.extract_pcd:
            pcd_path = os.path.join(self.save_folder(), cfg_output.pcd_filename)
            log.info("Extract point cloud")
            if VolumeType[self.config.alg_param.volume_type] == VolumeType.TSDFVoxelGrid:
                pcd = volume.cpu().extract_surface_points().to_legacy_point_cloud()
            else:
                pcd = volume.extract_point_cloud()
            o3d.io.write_point_cloud(pcd_path, pcd)
            log.info("Result saved to : {}".format(pcd_path))

    def _read_rgbd_memory(self, idx, create_rgbd=True, to_intensity=False):
        """combine a pair of RGB and depth images to a RGBD image

        :param idx: index of frame in the stream
        :param to_intensity: convert RGB to intensity
        :return: Open3D RGBD image
        """
        debug = self.config.settings.debug
        if debug:
            start_time = time.time()
        color = o3d.geometry.Image(self.bridge.cap_colorframe(idx))
        if debug:
            log.debug("--- %s seconds read RGB ---" % (time.time() - start_time))
        level = self.config.alg_param.depth_filter.level
        thresh = self.config.alg_param.depth_filter.delta_thresh

        if debug:
            start_time = time.time()
        depth = o3d.geometry.Image(self.bridge.filtered_depthframe(idx, level, thresh))
        if debug:
            log.debug("--- %s seconds read depth ---" % (time.time() - start_time))

        # align color image same size as depth image
        if debug:
            start_time = time.time()
        color = align_color2depth(color, depth)
        if debug:
            log.debug("--- %s seconds align RGB to depth ---" % (time.time() - start_time))

        rgbd = None
        if create_rgbd:
            if debug:
                start_time = time.time()
            rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
                color,
                depth,
                depth_scale=self.config.alg_param.depth_thresh.scale,
                depth_trunc=self.config.alg_param.depth_thresh.max,
                convert_rgb_to_intensity=to_intensity)
            if debug:
                log.debug("--- %s seconds create RGBD ---" % (time.time() - start_time))
        return color, depth, rgbd

    def read_depth_and_color_image(self, depth_input, color_input=None):
        depth = None
        color = None
        if isinstance(depth_input, str) and os.path.isfile(depth_input):
            depth = o3d.t.io.read_image(depth_input).to(self.device)
        elif isinstance(depth_input, int) and 0 <= depth_input < self._num_frames:
            level = self.config.alg_param.depth_filter.level
            thresh = self.config.alg_param.depth_filter.delta_thresh
            depth = o3d.geometry.Image(self.bridge.filtered_depthframe(depth_input, level, thresh))
        
        if isinstance(color_input, str) and os.path.isfile(color_input):
            color = o3d.t.io.read_image(color_input).to(self.device)
            color = color.resize(sampling_rate = depth.columns / color.columns)
        elif isinstance(color_input, int) and 0 <= color_input < self._num_frames:
            color = o3d.geometry.Image(self.bridge.cap_colorframe(color_input))
            color = align_color2depth(color, depth)
        
        return depth, color

    def _integrate_with_traj(self, volume):
        """integrate frames use input camera poses

        :param volume: integration volume
        :return: None
        """
        num_camera_pose = len(self._extrinsics)
        total = num_camera_pose
        if num_camera_pose != self._num_frames:
            total = min(num_camera_pose, self._num_frames)
            log.warning('Camera poses and frames have different length, only use first {:d} frames'.format(total))

        debug = self.config.settings.debug
        bar = Bar('Integration', max=int(total / self._skip_step), 
                  suffix='%(percent)d%% - %(index)d-th image added into the volume')
        for i in range(0, total, self._skip_step):
            bar.next()
            
            if debug:
                start_time = time.time()
            
            abs_idx = self._frame_i_abs[i]
            
            if 0 <= abs_idx < len(self._intrinsics):
                intrinsic = self._intrinsics[abs_idx]
            else:
                intrinsic = self._intrinsics[0]
            extrinsic = self._extrinsics[abs_idx]

            # read depth and color images
            depth = None
            rgb = None
            if os.path.isfile(self.config.input.depth_stream):
                if self.config.alg_param.integration.with_color:
                    depth, rgb = self.read_depth_and_color_image(abs_idx, abs_idx)
                else:
                    depth, rgb = self.read_depth_and_color_image(abs_idx)
                
                depth_raw = np.asarray(depth)
                if float(np.count_nonzero(depth_raw)) / depth_raw.size < self.config.alg_param.depth_filter.min_portion:
                    continue
            elif os.path.isdir(self.config.input.depth_stream):
                if self.config.alg_param.integration.with_color:
                    depth, rgb = self.read_depth_and_color_image(self._frame_files.depths[abs_idx], self._frame_files.colors[abs_idx])
                else:
                    depth, rgb = self.read_depth_and_color_image(self._frame_files.depths[abs_idx])
                depth_raw = depth.as_tensor()
                if float(len(depth_raw.nonzero()[0])) / (depth_raw.shape[0] * depth_raw.shape[1]) < self.config.alg_param.depth_filter.min_portion:
                    continue
            else:
                raise ValueError('Depth input stream is invalid')
            if debug:
                log.debug("--- %s seconds read images ---" % (time.time() - start_time))

            if VolumeType[self.config.alg_param.volume_type] == VolumeType.TSDFVoxelGrid:
                if debug:
                    tmp_time = time.time()
                if os.path.isfile(self.config.input.depth_stream):
                    if depth:
                        depth = o3d.t.geometry.Image.from_legacy_image(depth, self.device)
                    if rgb:
                        rgb = o3d.t.geometry.Image.from_legacy_image(rgb, self.device)
                extrinsic = o3d.core.Tensor(extrinsic, o3d.core.Dtype.Float64, self.device)
                intrinsic = o3d.core.Tensor(intrinsic, o3d.core.Dtype.Float64, self.device)
                if debug:
                    log.debug("--- %s seconds data to tensor ---" % (time.time() - tmp_time))
                    tmp_time = time.time()
                
                if rgb:
                    volume.integrate(depth, rgb, intrinsic, extrinsic,
                                    self.config.alg_param.depth_thresh.scale,
                                    self.config.alg_param.depth_thresh.max)
                else:
                    volume.integrate(depth, intrinsic, extrinsic,
                                    self.config.alg_param.depth_thresh.scale,
                                    self.config.alg_param.depth_thresh.max)
                    if debug:
                        log.debug("--- %s seconds integrate one frame ---" % (time.time() - tmp_time))
            else:
                if os.path.isdir(self.config.input.depth_stream):
                    if depth:
                        depth = depth.to_legacy_image()
                    if rgb:
                        rgb = rgb.to_legacy_image()

                assert rgb is not None, "ScalableTSDFVolume need color frames as input"

                rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
                        rgb,
                        depth,
                        depth_scale=self.config.alg_param.depth_thresh.scale,
                        depth_trunc=self.config.alg_param.depth_thresh.max,
                        convert_rgb_to_intensity=False)
                
                depth_raw = np.asarray(depth)
                
                K = intrinsic.flatten('F').tolist()
                o3d_intrinsic = o3d.camera.PinholeCameraIntrinsic(width = depth_raw.shape[1], height = depth_raw.shape[0], 
                                                               fx = K[0], fy = K[4], cx = K[6], cy = K[7])
                volume.integrate(rgbd, o3d_intrinsic, extrinsic)
                if debug:
                    log.debug("--- %s seconds integrate one frame ---" % (time.time() - tmp_time))
            if debug:
                log.debug("--- %s seconds ---" % (time.time() - start_time))

    def integrate(self):
        """volume integration of all RGBD frames with camera poses

        :return:None
        """
        parameters = self.config.alg_param
        if VolumeType[self.config.alg_param.volume_type] == VolumeType.TSDFVoxelGrid:
            volume = o3d.t.geometry.TSDFVoxelGrid(
                {
                    'tsdf': VoxelType[parameters.integration.voxel_type.tsdf].value,
                    'weight': VoxelType[parameters.integration.voxel_type.weight].value,
                    'color': VoxelType[parameters.integration.voxel_type.color].value
                },
                voxel_size=parameters.integration.voxel_len_fine,
                # sdf trunc need to be smaller than half block size
                sdf_trunc=min(parameters.integration.sdf_trunc,
                              parameters.integration.voxel_len_fine * 0.42 * parameters.integration.block_resolution),
                block_resolution=parameters.integration.block_resolution,
                block_count=parameters.integration.block_count,
                device=self.device
            )
        else:
            volume = o3d.pipelines.integration.ScalableTSDFVolume(
                voxel_length=parameters.integration.voxel_len_fine,
                sdf_trunc=parameters.integration.sdf_trunc,
                color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8,
            )
        
        self._integrate_with_traj(volume)
        self.export(volume)

    def run(self):
        """run reconstruction pipeline
        :return: None
        """
        # read camera extrinsics and intrinsics through bridge
        self._extrinsics, self._intrinsics = self.bridge.all_cameras()

        logging.info('start integration')
        self.integrate()
