import os
import open3d as o3d
import numpy as np
import logging
from collections import namedtuple
import logging

from multiscan.utils import io

FrameFiles = namedtuple('Frames', 'colors depths num')


def wrap_run(obj):
    return obj.run()


class MatchResult:
    """match result for two nodes in posegraph
    """
    def __init__(self, s, t, transform=np.identity(4)):
        """match result constructor

        :param s: index of source node
        :param t: index of target node
        :param transform: transformation from source node to target node
        """
        self.s = s
        self.t = t
        self.success = False
        self.transformation = transform
        self.information = np.identity(6)


class ReconBase:
    """base reconstruction class
    """

    def __init__(self, config, bridge=None):
        self.config = config
        self.bridge = bridge

    def read_images(self):
        """read input RGB and depth images

        :return: FrameFiles('colors depths num')
        """
        try:
            color_folder = self.config.input.color_stream
            depth_folder = self.config.input.depth_stream
            depth_files = []
            color_files = []
            if os.path.isdir(depth_folder):
                depth_files = io.get_file_list(depth_folder, ext='.png')
            if os.path.isdir(color_folder) and self.config.alg_param.integration.with_color:
                color_files = io.get_file_list(color_folder, ext='.png')
            list_len = len(depth_files)
            
            if list_len == 0:
                raise ValueError('The number of color and depth images is 0!')
            elif list_len != len(color_files) and self.config.alg_param.integration.with_color:
                logging.warning('The number of color and depth images does not match!')
                list_len = min(list_len, len(color_files))
                logging.warning(f'{list_len} number of images used')
            return FrameFiles(color_files, depth_files, list_len)
        except ValueError as e:
            logging.error(e)
        except IOError as e:
            logging.error(e)

    def read_intrinsic(self):
        return read_intrinsic(self.config.input.intrinsics_file)

    def save_folder(self):
        return self.config.output.save_folder

    def _frag_folder(self):
        return self.config.static_io.fragment.folder

    def _scene_folder(self):
        return self.config.static_io.scene.folder

    def frag_path(self):
        return os.path.join(self.save_folder(), self._frag_folder())

    def scene_path(self):
        return os.path.join(self.save_folder(), self._scene_folder())

    # def setting_path(self):
    #     setting_file = self.config.static_io.setting_file
    #     return os.path.join(self.save_folder(), setting_file)

    def parallel(self):
        return self.config.settings.parallel

    def run(self):
        """base run function, does nothing
        :return: None
        """
        pass


def read_intrinsic(intrinsic_file):
    """read camera intrinsic file

    :param width: width of input RGBD frame
    :param height: height of input RGBD frame
    :param intrinsic_file: intrinsic file path
    :return: Open3D camera intrinsic
    """
    default_intrinsic = o3d.camera.PinholeCameraIntrinsic(
        o3d.camera.PinholeCameraIntrinsicParameters.PrimeSenseDefault)
    if io.file_exist(intrinsic_file, '.json'):
        return o3d.io.read_pinhole_camera_intrinsic(intrinsic_file)
    elif intrinsic_file is '':
        logging.warning('No camera intrinsic input, default intrinsic was used')
    elif io.file_exist(intrinsic_file):
        ext = os.path.splitext(intrinsic_file)
        logging.warning('Extension {} is not supported, default intrinsic was used'.format(ext))
    else:
        logging.warning('File {} not exist, default intrinsic was used'.format(intrinsic_file))

    return default_intrinsic


def global_optimization(posegraph_path, optimized_posegraph_path,
                        max_cor_dist,
                        pref_loop_closure, debug=False):
    """global optimization of current posegraph

    :param posegraph_path: input file path to initial estimated posegraph
    :param optimized_posegraph_path: output file path for optimized posegraph
    :param max_cor_dist: distance value used for finding neighboring points when making information matrix
    :param pref_loop_closure: balancing parameter to decide odometry vs loop-closure
    :return: None
    """
    if debug:
    # to display messages from o3d.pipelines.registration.global_optimization
        o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Debug)
    method = o3d.pipelines.registration.GlobalOptimizationLevenbergMarquardt()
    criteria = o3d.pipelines.registration.GlobalOptimizationConvergenceCriteria()
    option = o3d.pipelines.registration.GlobalOptimizationOption(
        max_correspondence_distance=max_cor_dist,
        edge_prune_threshold=0.25,
        preference_loop_closure=pref_loop_closure,
        reference_node=0)
    pose_graph = o3d.io.read_pose_graph(posegraph_path)
    o3d.pipelines.registration.global_optimization(pose_graph, method, criteria, option)
    o3d.io.write_pose_graph(optimized_posegraph_path, pose_graph)
    o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)
