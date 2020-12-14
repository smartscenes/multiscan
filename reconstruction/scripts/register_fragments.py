from scripts.configure import Configure
import config.setting_pb2 as pb
from scripts.base import *
import functions.utils as utils


class RegisterFragment:
    def __init__(self, setting_path, ply_files, s, t):
        self._setting_path = setting_path
        self._ply_files = ply_files
        self._s = s
        self._t = t

        self._setting = None
        self.frag_path = None
        self.posegraph_optimized_file = None
        self._voxel_len = None
        self._debug = None

    def configure(self):
        """configure setting from setting file

        :return: None
        """
        config = Configure()
        config.load(self._setting_path)
        self._setting = config.setting
        save_folder = self._setting.io.save_folder
        frag_folder = self._setting.io.static_io.fragment.folder
        self.frag_path = os.path.join(save_folder, frag_folder)
        self.posegraph_optimized_file = self._setting.io.static_io.fragment.posegraph_optimized
        self._voxel_len = self._setting.parameters.integration.voxel_len_coarse
        self._debug = self._setting.common.debug

    def preprocess(self, pcd):
        """point cloud preprocessing, downsample and feature extraction

        :param pcd: point cloud
        :return: downsampled point cloud and extracted feature
        """
        pcd_down = pcd.voxel_down_sample(self._voxel_len)
        pcd_down.estimate_normals(
            o3d.geometry.KDTreeSearchParamHybrid(radius=self._voxel_len * 2.0,
                                                 max_nn=30))
        pcd_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
            pcd_down,
            o3d.geometry.KDTreeSearchParamHybrid(radius=self._voxel_len * 5.0,
                                                 max_nn=100))
        return pcd_down, pcd_fpfh

    def multiscale_icp(self, source, target, voxel_lens, max_iters, init_transform=np.identity(4)):
        """ICP with multiscale of voxel length and maximum iteration

        :param source: source point cloud
        :param target: target point cloud
        :param voxel_lens: voxel length pyramid
        :param max_iters: maximum iteration pyramid
        :param init_transform: initial transformation from source to target
        :return: [transformation information]
        """
        current_transform = init_transform
        result_icp = None
        information_matrix = None
        for i, scale in enumerate(range(len(max_iters))):  # multi-scale approach
            iter_c = max_iters[scale]
            dist_thresh = self._voxel_len * 1.4
            print("voxel_size %f" % voxel_lens[scale])
            source_down = source.voxel_down_sample(voxel_lens[scale])
            target_down = target.voxel_down_sample(voxel_lens[scale])
            icp_method = self._setting.parameters.icp_method
            if icp_method is pb.AlgParams.POINT2POINT:
                result_icp = o3d.pipelines.registration.registration_icp(
                    source_down, target_down, dist_thresh, current_transform,
                    o3d.pipelines.registration.TransformationEstimationPointToPoint(),
                    o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=iter_c))
            else:
                source_down.estimate_normals(
                    o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_lens[scale] * 2.0, max_nn=30))
                target_down.estimate_normals(
                    o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_lens[scale] * 2.0, max_nn=30))
                if icp_method is pb.AlgParams.POINT2PLANE:
                    result_icp = o3d.pipelines.registration.registration_icp(
                        source_down, target_down, dist_thresh, current_transform,
                        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
                        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=iter_c))
                elif icp_method == pb.AlgParams.COLOR:
                    result_icp = o3d.pipelines.registration.registration_colored_icp(
                        source_down, target_down, voxel_lens[scale], current_transform,
                        criteria=o3d.pipelines.registration.ICPConvergenceCriteria(
                            relative_fitness=1e-6,
                            relative_rmse=1e-6,
                            max_iteration=iter_c))
            current_transform = result_icp.transformation
            if i == len(max_iters) - 1:
                information_matrix = o3d.pipelines.registration.get_information_matrix_from_point_clouds(
                    source_down, target_down, voxel_lens[scale] * 1.4, result_icp.transformation)

        # TODO: debug mode visualization
        return result_icp.transformation, information_matrix

    def fpfh_register(self, source, target, source_fpfh, target_fpfh):
        """align source to target with extracted features

        :param source: source point cloud
        :param target: target point cloud
        :param source_fpfh: source point cloud feature
        :param target_fpfh: target point cloud feature
        :return: [success transformation information]
        """
        dist_thresh = self._voxel_len * 1.4
        global_registration = self._setting.parameters.global_registration
        result = None
        if global_registration == pb.AlgParams.FPFH:
            result = o3d.pipelines.registration.registration_fast_based_on_feature_matching(
                source, target, source_fpfh, target_fpfh,
                o3d.pipelines.registration.FastGlobalRegistrationOption(
                    maximum_correspondence_distance=dist_thresh))
        if global_registration == pb.AlgParams.RANSAC:
            result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
                source, target, source_fpfh, target_fpfh, dist_thresh,
                o3d.pipelines.registration.TransformationEstimationPointToPoint(False), 4, [
                    o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
                    o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(dist_thresh)],
                o3d.pipelines.registration.RANSACConvergenceCriteria(4000000, 500))
        if result.transformation.trace() == 4.0:
            return False, np.identity(4), np.zeros((6, 6))
        information = o3d.pipelines.registration.get_information_matrix_from_point_clouds(
            source, target, dist_thresh, result.transformation)
        if information[5, 5] / min(len(source.points), len(target.points)) < 0.3:
            return False, np.identity(4), np.zeros((6, 6))
        return True, result.transformation, information

    def init_registration(self, source_down, target_down, source_fpfh, target_fpfh):
        """estimate initial transformation from source to target point cloud

        :param source_down: downsampled source point cloud
        :param target_down: downsampled target point cloud
        :param source_fpfh: source point cloud feature
        :param target_fpfh: target point cloud feature
        :return: [success transformation information]
        """
        success = False
        if self._t == self._s + 1:  # odometry case
            utils.print_m("Using RGBD odometry")
            posegraph_frag = o3d.io.read_pose_graph(
                os.path.join(self.frag_path, self.posegraph_optimized_file % self._s))
            n_nodes = len(posegraph_frag.nodes)
            init_transform = np.linalg.inv(posegraph_frag.nodes[n_nodes - 1].pose)
            (transformation, information) = self.multiscale_icp(source_down, target_down, [self._voxel_len], [50],
                                                                init_transform)
        else:  # loop closure case
            (success, transformation, information) = self.fpfh_register(source_down, target_down, source_fpfh,
                                                                        target_fpfh)
            if not success:
                utils.print_m("No reasonable solution. Skip this pair")
                return success, np.identity(4), np.zeros((6, 6))
        utils.print_m(transformation)

        # TODO: debug mode visualization
        return success, transformation, information

    def run(self):
        """register a pair of point clouds

        :return: [success transformation information]
        """
        self.configure()
        print("reading %s ..." % self._ply_files[self._s])
        source = o3d.io.read_point_cloud(self._ply_files[self._s])
        print("reading %s ..." % self._ply_files[self._t])
        target = o3d.io.read_point_cloud(self._ply_files[self._t])
        (source_down, source_fpfh) = self.preprocess(source)
        (target_down, target_fpfh) = self.preprocess(target)
        (success, transformation, information) = self.init_registration(
            source_down, target_down, source_fpfh, target_fpfh)
        if self._t != self._s + 1 and not success:
            return False, np.identity(4), np.identity(6)

        if self._debug:
            utils.print_m(transformation)
            utils.print_m(information)

        return True, transformation, information


class RegisterFragments(ReconBase):
    def __init__(self, config):
        super().__init__(config)
        self._ply_files = None
        self.odometry = None
        self.posegraph = None

    def update_posegraph(self, s, t, transformation, information):
        """update posegraph

        :param s: index of source fragment
        :param t: index of target fragment
        :param transformation: 4x4 transformation matrix
        :param information: 6x6 information matrix from transformation matrix
        :return:
        """
        if t == s + 1:  # odometry case
            self.odometry = np.dot(transformation, self.odometry)
            odometry_inv = np.linalg.inv(self.odometry)
            self.posegraph.nodes.append(o3d.pipelines.registration.PoseGraphNode(odometry_inv))
            self.posegraph.edges.append(
                o3d.pipelines.registration.PoseGraphEdge(s, t, transformation, information, uncertain=False))
        else:  # loop closure case
            self.posegraph.edges.append(
                o3d.pipelines.registration.PoseGraphEdge(s, t, transformation, information, uncertain=True))

    def build_posegraph(self):
        """build posegraph

        :return: None
        """
        self.posegraph = o3d.pipelines.registration.PoseGraph()
        self.odometry = np.identity(4)
        self.posegraph.nodes.append(o3d.pipelines.registration.PoseGraphNode(self.odometry))
        num_files = len(self._ply_files)
        match_results = {}
        for s in range(num_files):
            for t in range(s + 1, num_files):
                match_results[s * num_files + t] = MatchResult(s, t)

        self.config.export(self.setting_path())
        if self.parallel():
            from joblib import Parallel, delayed
            import multiprocessing as mp

            registers = [RegisterFragment(self.setting_path(), self._ply_files, match_results[r].s, match_results[r].t)
                         for r in match_results]
            num_processes = min(mp.cpu_count(), max(len(match_results), 1))
            num_processes = min(num_processes, self.config.setting.parameters.cpu_num)
            results = Parallel(n_jobs=num_processes)(delayed(wrap_run)(register) for register in registers)

            for i, r in enumerate(match_results):
                match_results[r].success = results[i][0]
                match_results[r].transformation = results[i][1]
                match_results[r].information = results[i][2]

        else:
            for r in match_results:
                register_frag = RegisterFragment(
                    self.setting_path(), self._ply_files, match_results[r].s, match_results[r].t)
                (match_results[r].success, match_results[r].transformation, match_results[r].information) \
                    = register_frag.run()

        for r in match_results:
            if match_results[r].success:
                self.update_posegraph(
                    match_results[r].s, match_results[r].t,
                    match_results[r].transformation,
                    match_results[r].information)

        o3d.io.write_pose_graph(
            os.path.join(self.scene_path(), self.config.setting.io.static_io.scene.posegraph),
            self.posegraph)

    def optimize_posegraph(self):
        """ optimize pose graph

        :return: None
        """
        static_io = self.config.setting.io.static_io
        parameters = self.config.setting.parameters
        posegraph_path = os.path.join(self.scene_path(), static_io.scene.posegraph)
        optimized_posegraph_path = os.path.join(self.scene_path(), static_io.scene.posegraph_optimized)
        global_optimization(posegraph_path, optimized_posegraph_path,
                            max_cor_dist=parameters.integration.voxel_len_coarse * 1.4,
                            pref_loop_closure=parameters.optimization.pref_loop_closure_register)

    def run(self):
        """register fragments

        :return: None
        """
        print("Start register fragments.")
        o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Debug)
        self._ply_files = utils.get_file_list(self.frag_path(), ".ply")
        utils.make_clean_folder(self.scene_path())
        self.build_posegraph()
        self.optimize_posegraph()
