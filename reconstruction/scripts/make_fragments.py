from scripts.configure import Configure
from scripts.base import *
import functions.utils as utils

with_opencv = False


class MakeFragment:
    def __init__(self, setting_path, idx, frame_files, num_frags):
        self._setting_path = setting_path
        self._idx = idx
        self._frame_files = frame_files
        self._num_frags = num_frags

        self._setting = None
        self._intrinsic = None
        self._batch_size = None
        self._key_step = None
        self.frag_path = None
        self.posegraph_file = None
        self.posegraph_optimized_file = None
        self.pcd_file = None

    def configure(self):
        """configure setting from setting file

        :return: None
        """
        config = Configure()
        config.load(self._setting_path)
        self._setting = config.setting
        depth = o3d.io.read_image(self._frame_files.depths[0])
        depth_data = np.asarray(depth)
        width = np.shape(depth_data)[1]
        height = np.shape(depth_data)[0]
        print(width, height)
        self._intrinsic = read_intrinsic(self._setting.io.intrinsic_path, width, height)
        self._batch_size = self._setting.parameters.frames.batch_size
        self._key_step = self._setting.parameters.frames.key_step

        save_folder = self._setting.io.save_folder
        frag_folder = self._setting.io.static_io.fragment.folder
        self.frag_path = os.path.join(save_folder, frag_folder)
        self.posegraph_file = self._setting.io.static_io.fragment.posegraph
        self.posegraph_optimized_file = self._setting.io.static_io.fragment.posegraph_optimized
        self.pcd_file = self._setting.io.static_io.fragment.pcd

    def read_rgbd(self, color_file, depth_file, to_intensity=False):
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
            depth_trunc=self._setting.parameters.depth_thresh.max,
            convert_rgb_to_intensity=to_intensity)
        return rgbd

    def pair_register(self, s, t):
        """estimate initial transformation from source to target frame

        :param s: index of source frame
        :param t: index of target frame
        :return: [success transformation information]
        """
        source_rgbd = self.read_rgbd(self._frame_files.colors[s], self._frame_files.depths[s], True)
        target_rgbd = self.read_rgbd(self._frame_files.colors[t], self._frame_files.depths[t], True)
        option = o3d.pipelines.odometry.OdometryOption()
        option.max_depth_diff = self._setting.parameters.depth_thresh.diff
        if abs(s - t) is not 1:
            # TODO: add with opencv
            # if with_opencv:
            #     success_5pt, odo_init = pose_estimation(source_rgbd,
            #                                             target_rgbd,
            #                                             self._intrinsic, False)
            #     if success_5pt:
            #         [success, trans, info] = o3d.pipelines.odometry.compute_rgbd_odometry(
            #             source_rgbd, target_rgbd, self._intrinsic, odo_init,
            #             o3d.pipelines.odometry.RGBDOdometryJacobianFromHybridTerm(), option)
            #         return [success, trans, info]
            return [False, np.identity(4), np.identity(6)]
        else:
            odo_init = np.identity(4)
            [success, trans, info] = o3d.pipelines.odometry.compute_rgbd_odometry(
                source_rgbd, target_rgbd, self._intrinsic, odo_init,
                o3d.pipelines.odometry.RGBDOdometryJacobianFromHybridTerm(), option)
            return [success, trans, info]

    def optimize_posegraph(self):
        """ optimize pose graph

        :return: None
        """
        posegraph_path = os.path.join(self.frag_path, self.posegraph_file % self._idx)
        optimized_posegraph_path = os.path.join(self.frag_path, self.posegraph_optimized_file % self._idx)
        global_optimization(posegraph_path, optimized_posegraph_path,
                            max_cor_dist=self._setting.parameters.optimization.max_correspond_dist,
                            pref_loop_closure=self._setting.parameters.optimization.pref_loop_closure_odometry)

    def build_pointcloud(self):
        """reconstruct the point cloud of a batch of frames

        :return: None
        """
        file_path = os.path.join(self.frag_path, self.posegraph_optimized_file % self._idx)
        pose_graph = o3d.io.read_pose_graph(file_path)
        volume = o3d.pipelines.integration.ScalableTSDFVolume(
            voxel_length=self._setting.parameters.integration.volume_len / 512.0,
            sdf_trunc=0.04,
            color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8)
        for i in range(len(pose_graph.nodes)):
            i_abs = self._idx * self._batch_size + i
            print(
                "Fragment %03d / %03d :: integrate rgbd frame %d (%d of %d)." %
                (self._idx, self._num_frags - 1, i_abs, i + 1, len(pose_graph.nodes)))
            rgbd = self.read_rgbd(self._frame_files.colors[i_abs], self._frame_files.depths[i_abs], False)
            pose = pose_graph.nodes[i].pose
            volume.integrate(rgbd, self._intrinsic, np.linalg.inv(pose))
        mesh = volume.extract_triangle_mesh()
        mesh.compute_vertex_normals()
        pcd = o3d.geometry.PointCloud()
        pcd.points = mesh.vertices
        pcd.colors = mesh.vertex_colors
        pcd_path = os.path.join(self.frag_path, self.pcd_file % self._idx)
        o3d.io.write_point_cloud(pcd_path, pcd, False, True)

    def build_posegraph(self, s_idx, e_idx):
        """build a posegraph for a single fragment reconstruction

        :param s_idx: index of the start frame
        :param e_idx: index of the end frame
        :return: None
        """
        o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)
        pose_graph = o3d.pipelines.registration.PoseGraph()
        trans_odometry = np.identity(4)
        pose_graph.nodes.append(o3d.pipelines.registration.PoseGraphNode(trans_odometry))

        for s in range(s_idx, e_idx):
            for t in range(s + 1, e_idx):
                # odometry case
                if t == s + 1:
                    utils.print_m(
                        "Fragment %03d / %03d :: RGBD matching between frame : %d and %d"
                        % (self._idx, self._num_frags - 1, s, t))
                    [success, trans, info] = self.pair_register(s, t)
                    trans_odometry = np.dot(trans, trans_odometry)
                    trans_odometry_inv = np.linalg.inv(trans_odometry)
                    pose_graph.nodes.append(
                        o3d.pipelines.registration.PoseGraphNode(trans_odometry_inv))
                    pose_graph.edges.append(
                        o3d.pipelines.registration.PoseGraphEdge(s - s_idx, t - s_idx,
                                                       trans, info,
                                                       uncertain=False))
                # loop closure case
                if s % self._key_step == 0 and t % self._key_step == 0:
                    utils.print_m(
                        "Fragment %03d / %03d :: RGBD matching between frame : %d and %d"
                        % (self._idx, self._num_frags - 1, s, t))
                    [success, trans, info] = self.pair_register(s, t)
                    if success:
                        pose_graph.edges.append(
                            o3d.pipelines.registration.PoseGraphEdge(s - s_idx, t - s_idx,
                                                           trans, info,
                                                           uncertain=True))
        o3d.io.write_pose_graph(
            os.path.join(self.frag_path, self.posegraph_file % self._idx),
            pose_graph)

    def run(self):
        """reconstruct a number of frames into a fragment point cloud

        :return: None
        """
        self.configure()
        s_idx = self._idx * self._batch_size
        e_idx = min(s_idx + self._batch_size, self._frame_files.num)
        self.build_posegraph(s_idx, e_idx)
        self.optimize_posegraph()
        self.build_pointcloud()


class MakeFragments(ReconBase):
    """make point cloud fragments from input sequence of RGBD frames
    """
    def __init__(self, config, frame_files=None):
        super().__init__(config)

        if frame_files is None:
            self._frame_files = self.read_images()
        else:
            self._frame_files = frame_files

    def run(self):
        """Divide a sequence of images into batches and reconstruct fragments

        :return: None
        """
        print("Start Making fragments from the RGBD sequence.")
        batch_size = self.config.setting.parameters.frames.batch_size
        utils.make_clean_folder(self.frag_path())
        try:
            num_frags = int(np.ceil(float(self._frame_files.num)) / batch_size)
        except ValueError as e:
            utils.print_e(e)
            raise

        self.config.export(self.setting_path())
        if self.parallel() and num_frags:
            import multiprocessing as mp
            from joblib import Parallel, delayed

            makes = [MakeFragment(self.setting_path(), idx, self._frame_files, num_frags) for idx in
                     range(num_frags)]
            num_processes = min(mp.cpu_count(), num_frags)
            num_processes = min(num_processes, self.config.setting.parameters.cpu_num)
            Parallel(n_jobs=num_processes)(delayed(wrap_run)(make)
                                           for make in makes)

        else:
            for idx in range(num_frags):
                make = MakeFragment(self.setting_path(), idx, self._frame_files, num_frags)
                make.run()
