from scripts.base import ReconBase
from scripts.make_fragments import MakeFragments
from scripts.register_fragments import RegisterFragments
from scripts.refine_registration import RefineRegistration
import functions.utils as utils
import numpy as np
import open3d as o3d
import os

class Reconstruct(ReconBase):
    """reconstruction class
    input a sequence of RGBD images, output a point cloud or a mesh
    """

    def __init__(self, config, bridge=None):
        super().__init__(config, bridge)
        self._trajectory = None
        if bridge is None:
            self._frame_files = self.read_images()
            self._num_frames = self._frame_files.num
            self._intrinsic = self.read_intrinsic()
        else:
            self._num_frames = bridge.meta['num_frames']
            self._intrinsics = None

    def export(self, volume):
        """export reconstruction results

        :param volume: integration volume
        :return: None
        """
        common = self.config.setting.common
        io = self.config.setting.io
        if not os.path.isdir(self.save_folder()):
            os.makedirs(self.save_folder())
        if common.extract_mesh:
            mesh_path = os.path.join(self.save_folder(), io.mesh_filename)
            utils.print_m("Extract triangle mesh")
            mesh = volume.extract_triangle_mesh()
            o3d.io.write_triangle_mesh(mesh_path, mesh)
            utils.print_m("Result saved to : {}".format(mesh_path))
        if common.extract_pcd:
            pcd_path = os.path.join(self.save_folder(), io.pcd_filename)
            utils.print_m("Extract point cloud")
            pcd = volume.extract_point_cloud()
            o3d.io.write_point_cloud(pcd_path, pcd)
            utils.print_m("Result saved to : {}".format(pcd_path))
        
        # save_intrinsic_path = os.path.join(self.save_folder(), self.config.setting.io.intrinsic)
        # o3d.io.write_pinhole_camera_intrinsic(save_intrinsic_path, self._intrinsic)
        # self._write_trajectory()

    def _read_rgbd_memory(self, idx, to_intensity=False):
        """combine a pair of RGB and depth images to a RGBD image

        :param idx: index of frame in the stream
        :param to_intensity: convert RGB to intensity
        :return: Open3D RGBD image
        """
        color = o3d.geometry.Image(self.bridge.cap_colorframe(idx))
        level = self.config.setting.parameters.filter.level
        thresh= self.config.setting.parameters.filter.delta_thresh
        depth = o3d.geometry.Image(self.bridge.filtered_depthframe(idx, level, thresh))

        # align color image same size as depth image
        color = utils.align_color2depth(color, depth)

        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            color,
            depth,
            depth_trunc=self.config.setting.parameters.depth_thresh.max,
            convert_rgb_to_intensity=to_intensity)
        return rgbd
    
    def _read_rgbd_file(self, color_file, depth_file, to_intensity=False):
        """combine a pair of RGB and depth images to a RGBD image

        :param color_file: color image file path
        :param depth_file: depth image file path
        :param to_intensity: convert RGB to intensity
        :return: Open3D RGBD image
        """
        color = o3d.io.read_image(color_file)
        depth = o3d.io.read_image(depth_file)
        # align color image same size as depth image
        color = utils.align_color2depth(color, depth)

        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(
            color,
            depth,
            depth_trunc=self.config.setting.parameters.depth_thresh.max,
            convert_rgb_to_intensity=to_intensity)
        return rgbd

    def _read_traj_impl(self, trajectory_file=None):
        """implementation of read trajectory from .log file

        :param trajectory_file: trajectory file path
        :return: None
        """
        self._trajectory = []
        with open(trajectory_file, 'r') as f:
            meta_str = f.readline()
            while meta_str:
                metadata = list(map(int, meta_str.split()))
                mat = np.zeros(shape=(4, 4))
                for i in range(4):
                    mat_str = f.readline()
                    mat[i, :] = np.fromstring(mat_str, dtype=float, sep=' \t')
                self._trajectory.append(mat)
                meta_str = f.readline()

    def read_trajectory(self, trajectory_file=None):
        """read camera poses, if file is empty, will estimate the camera trajectory

        :param trajectory_file: trajectory file path
        :type trajectory_file: .log
        :return: None
        """
        if utils.file_exist(trajectory_file, '.log'):
            self._read_traj_impl(trajectory_file)
        elif utils.folder_exist(trajectory_file):
            save_traj_path = os.path.join(self.save_folder(), self.config.setting.io.trajectory)
            with open(save_traj_path, "w+") as save_file:
                traj_files = utils.get_file_list(trajectory_file, '.txt')
                for i in range(len(traj_files)):
                    save_file.write("{} {} {}".format(i, i, i + 1))
                    save_file.write("\n")
                    with open(traj_files[i]) as file:
                        lines = file.readlines()
                    for line in lines:
                        save_file.write(line.strip())
                        save_file.write("\n")
            self._read_traj_impl(save_traj_path)
        elif trajectory_file != '':
            utils.print_w('Trajectory {} not exist, will estimate the trajectory'.format(trajectory_file))

    def _write_trajectory(self):
        """write the trajectory into a .log file

        :return: None
        """
        save_traj_path = os.path.join(self.save_folder(), self.config.setting.io.trajectory)
        with open(save_traj_path, 'w+') as f:
            for i, pose in enumerate(self._trajectory):
                f.write('{} {} {}\n'.format(i, i, i + 1))
                f.write('{0:.8f} {1:.8f} {2:.8f} {3:.8f}\n'.format(
                    pose[0, 0], pose[0, 1], pose[0, 2], pose[0, 3]))
                f.write('{0:.8f} {1:.8f} {2:.8f} {3:.8f}\n'.format(
                    pose[1, 0], pose[1, 1], pose[1, 2], pose[1, 3]))
                f.write('{0:.8f} {1:.8f} {2:.8f} {3:.8f}\n'.format(
                    pose[2, 0], pose[2, 1], pose[2, 2], pose[2, 3]))
                f.write('{0:.8f} {1:.8f} {2:.8f} {3:.8f}\n'.format(
                    pose[3, 0], pose[3, 1], pose[3, 2], pose[3, 3]))

    def _integrate_with_traj(self, volume):
        """integrate frames use input camera poses

        :param volume: integration volume
        :return: None
        """
        traj_len = len(self._trajectory)
        step = self.config.setting.parameters.step
        total = traj_len
        if traj_len != self._num_frames:
            total = min(traj_len, self._num_frames)
            utils.print_w('Trajectory and frames have different length, only use first {:d} frames'.format(total))
        for i in range(0, total, step):
            print("Integrate {:d}-th image into the volume.".format(int(i/step)))
            if self.bridge:
                rgbd = self._read_rgbd_memory(i)
            else:
                rgbd = self._read_rgbd_file(self._frame_files.colors[i], self._frame_files.depths[i])
            volume.integrate(rgbd, self._intrinsics[i], np.linalg.inv(self._trajectory[i]))

    def _integrate_no_traj(self, volume):
        """integrate frames use estimated camera poses from posegraph

        :param volume: integration volume
        :return: None
        """
        self._trajectory = []
        num_frags = 0
        batch_size = self.config.setting.parameters.frames.batch_size
        try:
            num_frags = int(np.ceil(float(self._frame_files.num)) / batch_size)
        except ValueError as e:
            utils.print_e(e)
        posegraph_refined = o3d.io.read_pose_graph(
            os.path.join(self.scene_path(), self.config.setting.io.static_io.scene.refined_optimized_posegraph))

        for frag_i in range(len(posegraph_refined.nodes)):
            posegraph_frag = o3d.io.read_pose_graph(
                os.path.join(self.frag_path(), self.config.setting.io.static_io.fragment.posegraph_optimized % frag_i))
            for frame_i in range(len(posegraph_frag.nodes)):
                frame_i_abs = frag_i * batch_size + frame_i
                print("Fragment %03d / %03d :: integrate rgbd frame %d (%d of %d)." % (
                    frag_i, num_frags - 1, frame_i_abs, frame_i + 1, len(posegraph_frag.nodes)))
                rgbd = self._read_rgbd_file(
                    self._frame_files.colors[frame_i_abs], self._frame_files.depths[frame_i_abs])
                pose = np.dot(posegraph_refined.nodes[frag_i].pose, posegraph_frag.nodes[frame_i].pose)
                volume.integrate(rgbd, self._intrinsic, np.linalg.inv(pose))
                self._trajectory.append(pose)

    def integrate(self):
        """volume integration of all RGBD frames will camera poses

        :return:None
        """
        parameters = self.config.setting.parameters
        volume = o3d.pipelines.integration.ScalableTSDFVolume(
            voxel_length=parameters.integration.voxel_len_fine / 512.0,
            sdf_trunc=parameters.integration.sdf_trunc,
            color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8,
        )
        if self._trajectory is None:
            self._integrate_no_traj(volume)
        else:
            self._integrate_with_traj(volume)

        self.export(volume)

    def run(self):
        """run reconstruction pipeline
        :return: None
        """
        if self.bridge:
            self._trajectory, self._intrinsics = self.bridge.all_cameras()
        else:
            self.read_trajectory(self.config.setting.io.trajectory_path)

        # if no trajectory input go through Open3D reconstruction pipeline
        # else has trajectory input integrate RGBD images directory
        if self._trajectory is None:
            make_fragment = MakeFragments(self.config, self._frame_files)
            make_fragment.run()
            register_fragments = RegisterFragments(self.config)
            register_fragments.run()
            refine_registration = RefineRegistration(self.config)
            refine_registration.run()

        self.integrate()
