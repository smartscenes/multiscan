from scripts.register_fragments import *


class RefinePair(RegisterFragment):
    def __init__(self, setting_path, ply_files, s, t, transform):
        super().__init__(setting_path, ply_files, s, t)
        self._transform = transform

    def refine(self, source, target, init_transform):
        """ multiscale icp refinement

        :param source: source fragment
        :param target: target fragment
        :param init_transform: initial estimation of transformation matrix
        :return: [success, transformation, information]
        """
        (transformation, information) = self.multiscale_icp(
            source, target,
            [self._voxel_len, self._voxel_len / 2.0, self._voxel_len / 4.0], [50, 30, 14],
            init_transform)

        # TODO: debug mode visualization
        return True, transformation, information

    def run(self):
        """refine registration of a pair of fragment

        :return: [success, transformation, information]
        """
        self.configure()
        print("reading %s ..." % self._ply_files[self._s])
        source = o3d.io.read_point_cloud(self._ply_files[self._s])
        print("reading %s ..." % self._ply_files[self._t])
        target = o3d.io.read_point_cloud(self._ply_files[self._t])
        (success, transformation, information) = self.refine(source, target, self._transform)

        if self._debug:
            utils.print_m(transformation)
            utils.print_m(information)

        return success, transformation, information


class RefineRegistration(RegisterFragments):
    def __init__(self, config):
        super().__init__(config)

    def build_posegraph(self):
        """build posegraph

        :return: None
        """
        static_io = self.config.setting.io.static_io
        self.posegraph = o3d.io.read_pose_graph(os.path.join(self.scene_path(), static_io.scene.posegraph_optimized))

        num_files = len(self._ply_files)
        match_results = {}
        for edge in self.posegraph.edges:
            s = edge.source_node_id
            t = edge.target_node_id
            match_results[s * num_files + t] = MatchResult(s, t, edge.transformation)

        self.config.export(self.setting_path())
        if self.parallel():
            from joblib import Parallel, delayed
            import multiprocessing as mp

            refines = [RefinePair(self.setting_path(), self._ply_files, match_results[r].s, match_results[r].t,
                                  match_results[r].transformation)
                       for r in match_results]
            num_processes = min(mp.cpu_count(), max(len(match_results), 1))
            num_processes = min(num_processes, self.config.setting.parameters.cpu_num)
            results = Parallel(n_jobs=num_processes)(delayed(wrap_run)(refine) for refine in refines)

            for i, r in enumerate(match_results):
                match_results[r].success = results[i][0]
                match_results[r].transformation = results[i][1]
                match_results[r].information = results[i][2]

        else:
            for r in match_results:
                refine = RefinePair(
                    self.setting_path(), self._ply_files, match_results[r].s, match_results[r].t,
                    match_results[r].transformation)
                (match_results[r].success, match_results[r].transformation, match_results[r].information) \
                    = refine.run()

        self.posegraph = o3d.pipelines.registration.PoseGraph()
        self.odometry = np.identity(4)
        self.posegraph.nodes.append(o3d.pipelines.registration.PoseGraphNode(self.odometry))
        for r in match_results:
            if match_results[r].success:
                self.update_posegraph(
                    match_results[r].s, match_results[r].t,
                    match_results[r].transformation,
                    match_results[r].information)

        o3d.io.write_pose_graph(
            os.path.join(self.scene_path(), self.config.setting.io.static_io.scene.refined_posegraph),
            self.posegraph)

    def optimize_posegraph(self):
        """ optimize pose graph

        :return: None
        """
        static_io = self.config.setting.io.static_io
        parameters = self.config.setting.parameters
        posegraph_path = os.path.join(self.scene_path(), static_io.scene.refined_posegraph)
        optimized_posegraph_path = os.path.join(self.scene_path(), static_io.scene.refined_optimized_posegraph)
        global_optimization(posegraph_path, optimized_posegraph_path,
                            max_cor_dist= parameters.integration.voxel_len_coarse * 1.4,
                            pref_loop_closure=parameters.optimization.pref_loop_closure_register)

    def run(self):
        """refine fragments registration results

        :return: None
        """
        print("Start refine rough registration of fragments.")
        o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Debug)
        self._ply_files = utils.get_file_list(self.frag_path(), ".ply")
        self.build_posegraph()
        self.optimize_posegraph()
