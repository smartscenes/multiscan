import argparse
import os
import logging
from enum import Enum

import numpy as np
import open3d as o3d

from multiscan.utils import io
from multiscan.meshproc import TriMesh


log = logging.getLogger(__name__)


class ICPType(Enum):
    POINT2POINT = "POINT2POINT"
    POINT2PLANE = "POINT2PLANE"
    COLOR = "COLOR"

def pick_points(pcd, width=640, height=480):
    vis = o3d.visualization.VisualizerWithEditing()
    vis.create_window(window_name='Pick Points', width=width, height=height, visible=True)
    vis.add_geometry(pcd)
    vis.run()
    vis.destroy_window()
    return vis.get_picked_points()

def procrustes(source_points, target_points):
    s_rows, s_cols = np.shape(source_points)
    t_rows, t_cols = np.shape(target_points)
    assert s_rows == t_rows and s_cols == t_cols
    row = s_rows

    s_orig = np.mean(source_points, axis=0)
    t_orig = np.mean(target_points, axis=0)

    s_centered = source_points - s_orig
    t_centered = target_points - t_orig

    ssq_s = np.sum(s_centered * s_centered, axis=0)
    ssq_t = np.sum(t_centered * t_centered, axis=0)

    s_same = np.all((ssq_s - np.finfo(float).eps * row * (s_orig * s_orig)) <= 0 )
    t_same = np.all((ssq_t - np.finfo(float).eps * row * (t_orig * t_orig)) <= 0 )

    transformation = np.identity(4)
    error = -1
    if not s_same and not t_same:
        s_norm = np.sqrt(np.sum(ssq_s))
        t_norm = np.sqrt(np.sum(ssq_t))

        s_centered = s_centered / s_norm
        t_centered = t_centered / t_norm

        affine = np.dot(t_centered.transpose(), s_centered)
        u, s, vh = np.linalg.svd(affine, full_matrices=False)

        rotation = np.dot(vh, u.transpose())
        trace_s = np.sum(s)

        scale = trace_s * t_norm / s_norm
        scale = 1
        error = 1 - trace_s**2
        translation = t_orig.transpose() - scale * np.dot(s_orig.transpose(), rotation)

        rotation_mat = np.identity(4)
        rotation_mat[:3, :3] = rotation
        translation_mat = np.identity(4)
        translation_mat[:3, 3] = translation

        transformation = np.dot(translation_mat, np.dot(transformation, rotation_mat))

    return transformation, error


# TODO: make params configurable
class ICP:
    def __init__(self, source, target, params, icp_method=ICPType.COLOR):
        self._voxel_len = params['voxel_len']
        self._normal_estimation_radius = params['normal_estimation_radius']
        self._normal_estimation_knn = params['normal_estimation_knn']
        self.params = params
        self.source = source
        self.target = target
        self.source_down = None
        self.target_down = None
        self.icp_method = icp_method

    def viz(self, output=None, width=640, height=480, transformation=np.identity(4), display=True):
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name='PCD', width=width, height=height, visible=True)
        self.source.paint_uniform_color(np.array([1.0, 0.0, 0.0]))
        vis.add_geometry(self.source)
        self.target.paint_uniform_color(np.array([0.0, 1.0, 0.0]))
        self.target.transform(np.linalg.inv(transformation))
        vis.add_geometry(self.target)
        if output:
            vis.capture_screen_image(filename=output, do_render=True)
        if display:
            vis.run()
        vis.destroy_window()

        del vis

    def preprocess(self, pcd, fpfh_feature_radius, fpfh_feature_knn):
        """point cloud preprocessing, downsample and feature extraction

        :param pcd: point cloud
        :return: downsampled point cloud and extracted feature
        """
        pcd_down = pcd.voxel_down_sample(self._voxel_len)
        pcd_down.estimate_normals(
            o3d.geometry.KDTreeSearchParamHybrid(radius=self._voxel_len * self._normal_estimation_radius,
                                                 max_nn=self._normal_estimation_knn))
        pcd_fpfh = o3d.pipelines.registration.compute_fpfh_feature(
            pcd_down,
            o3d.geometry.KDTreeSearchParamHybrid(radius=self._voxel_len * fpfh_feature_radius,
                                                 max_nn=fpfh_feature_knn))
        return pcd_down, pcd_fpfh

    def fpfh_register(self, fpfh_max_distance, ransac=False):
        (self.source_down, source_fpfh) = self.preprocess(self.source, self.params['fpfh_feature_radius'], self.params['fpfh_feature_knn'])
        (self.target_down, target_fpfh) = self.preprocess(self.target, self.params['fpfh_feature_radius'], self.params['fpfh_feature_knn'])
        source = self.source_down
        target = self.target_down
        dist_thresh = self._voxel_len * fpfh_max_distance
        if not ransac:
            result = o3d.pipelines.registration.registration_fast_based_on_feature_matching(
                source, target, source_fpfh, target_fpfh,
                o3d.pipelines.registration.FastGlobalRegistrationOption(
                    maximum_correspondence_distance=dist_thresh))
        else:
            ransac_n = 4
            edge_len = 0.9
            max_iteration = 4000000
            confidence = 0.99
            result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
                source, target, source_fpfh, target_fpfh, True, dist_thresh,
                o3d.pipelines.registration.TransformationEstimationPointToPoint(False), ransac_n, 
                [
                    o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(edge_len),
                    o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(dist_thresh)
                ],
                o3d.pipelines.registration.RANSACConvergenceCriteria(max_iteration, confidence))
        if result.transformation.trace() == 4.0:
            return False, np.identity(4), np.zeros((6, 6))
        information = o3d.pipelines.registration.get_information_matrix_from_point_clouds(
            source, target, dist_thresh, result.transformation)
        if information[5, 5] / min(len(source.points), len(target.points)) < 0.3:
            return False, np.identity(4), np.zeros((6, 6))
        return True, result.transformation, information

    def multiscale_icp(self, voxel_lens, max_iters, max_correspondence_distance, init_transform=np.identity(4)):
        """ICP with multiscale of voxel length and maximum iteration

        :param source: source point cloud
        :param target: target point cloud
        :param voxel_lens: voxel length pyramid
        :param max_iters: maximum iteration pyramid
        :param init_transform: initial transformation from source to target
        :return: [transformation information]
        """
        source = self.source
        target = self.target
        current_transform = init_transform
        result_icp = None
        information_matrix = None
        for i, scale in enumerate(range(len(max_iters))):  # multi-scale approach
            iter_c = max_iters[scale]
            dist_thresh = self._voxel_len * max_correspondence_distance
            source_down = source.voxel_down_sample(voxel_lens[scale])
            target_down = target.voxel_down_sample(voxel_lens[scale])
            icp_method = self.icp_method
            if icp_method is ICPType.POINT2POINT:
                result_icp = o3d.pipelines.registration.registration_icp(
                    source_down, target_down, dist_thresh, current_transform,
                    o3d.pipelines.registration.TransformationEstimationPointToPoint(),
                    o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=iter_c))
            else:
                source_down.estimate_normals(
                    o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_lens[scale] * self._normal_estimation_radius, 
                                                         max_nn=self._normal_estimation_knn))
                target_down.estimate_normals(
                    o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_lens[scale] * self._normal_estimation_radius, 
                                                         max_nn=self._normal_estimation_knn))
                if icp_method is ICPType.POINT2PLANE:
                    result_icp = o3d.pipelines.registration.registration_icp(
                        source_down, target_down, dist_thresh, current_transform,
                        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
                        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=iter_c))
                elif icp_method == ICPType.COLOR:
                    result_icp = o3d.pipelines.registration.registration_colored_icp(
                        source_down, target_down, voxel_lens[scale], current_transform,
                        criteria=o3d.pipelines.registration.ICPConvergenceCriteria(
                            relative_fitness=1e-6,
                            relative_rmse=1e-6,
                            max_iteration=iter_c))
            current_transform = result_icp.transformation
            if i == len(max_iters) - 1:
                information_matrix = o3d.pipelines.registration.get_information_matrix_from_point_clouds(
                    source_down, target_down, voxel_lens[scale] * max_correspondence_distance, result_icp.transformation)

        return result_icp.transformation, information_matrix

    def align(self, voxel_length_pyramid, max_iter_pyramid, tans_init=None):
        if tans_init is None:
            (success, tans_init, information) = self.fpfh_register(self.params['fpfh_max_distance'])
        else:
            success = True
        voxel_lengths = [self._voxel_len] * len(voxel_length_pyramid)
        voxel_lengths = np.asarray(voxel_lengths) / np.asarray(voxel_length_pyramid)
        if success:
            (transformation, information) = self.multiscale_icp(voxel_lengths, max_iter_pyramid, 
                                                                self.params['max_correspondence_distance'], tans_init)

        return success, transformation, information

def align_pairs(sid, tid, source_mesh_path, targe_mesh_path, params, output_filename):
    if not os.path.isfile(source_mesh_path) or not os.path.isfile(targe_mesh_path):
        return None

    trimesh1 = TriMesh(source_mesh_path)

    trimesh2 = TriMesh(targe_mesh_path)

    source = o3d.geometry.PointCloud(trimesh1.o3d_mesh.vertices)
    source.colors = trimesh1.o3d_mesh.vertex_colors
    target = o3d.geometry.PointCloud(trimesh2.o3d_mesh.vertices)
    target.colors = trimesh2.o3d_mesh.vertex_colors

    trans_init = None
    if params['pick_points'] or params.get('corres', None):
        if params['pick_points']:
            picked_id_source = pick_points(source)
            picked_id_target = pick_points(target)
            log.debug(picked_id_source)
            log.debug(picked_id_target)

            # save picked points to file
            picked_points = {}
            picked_points['source_id'] = sid
            picked_points['target_id'] = tid
            picked_points['source_picked_point_idx'] = picked_id_source
            picked_points['target_picked_point_idx'] = picked_id_target
            picked_points['source_picked_points'] = np.asarray(source.points)[picked_id_source].tolist()
            picked_points['target_picked_points'] = np.asarray(target.points)[picked_id_target].tolist()
            picked_points_filename = os.path.join(os.path.dirname(output_filename), f'{sid}_to_{tid}_align_corres.json')
            io.write_json(picked_points, picked_points_filename)
            log.info(f'picked points saved to {picked_points_filename}')
        elif params.get('corres', None):
            input_corres = io.read_json(params['corres'])
            assert input_corres is not None
            picked_id_source = input_corres['source_picked_point_idx']
            picked_id_target = input_corres['target_picked_point_idx']

        assert (len(picked_id_source) >= 3 and len(picked_id_target) >= 3)
        assert (len(picked_id_source) == len(picked_id_target))
        corr = np.zeros((len(picked_id_source), 2))
        corr[:, 0] = picked_id_source
        corr[:, 1] = picked_id_target
        p2p = o3d.pipelines.registration.TransformationEstimationPointToPoint()
        trans_init = p2p.compute_transformation(source, target, o3d.utility.Vector2iVector(corr))

    icp = ICP(source, target, params, ICPType[params['icp_type']])
    (success, transformation, information) = icp.align(params['voxel_length_pyramid'], params['max_iter_pyramid'], trans_init)

    output = {}
    output['version'] = 'pairalign@0.0.1'
    
    if success:
        # TODO: make mesh path configurable
        output['target_id'] = tid
        output['s2t_transformation'] = transformation.flatten(order='F').tolist()
        output['error_matrix'] = information.flatten(order='F').tolist()

        base_dir = os.path.dirname(output_filename)
        # TODO: make output path configurable
        viz_img1 = os.path.join(base_dir, sid + '_prealign.png')
        viz_img2 = os.path.join(base_dir, sid + '_postalign.png')
        log.info(f'prealign image saved to {viz_img1}')
        log.info(f'postalign image saved to {viz_img2}')
        icp.viz(viz_img1, params['width'], params['height'], display=False)
        icp.viz(viz_img2, params['width'], params['height'], transformation, False)
    else:
        log.warning(f'postalign failed')
        return None
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pairwise alignment!')
    parser.add_argument('-sid', '--source_id', dest='source_id', type=str, action='store', required=True,
                        help='Input source scan id')
    parser.add_argument('-tid', '--target_id', dest='target_id', type=str, action='store', required=True,
                        help='Input target scan id')
    parser.add_argument('-s', '--source_mesh', dest='source_mesh', type=str, action='store', required=True,
                        help='Input ply source mesh filepath')
    parser.add_argument('-t', '--target_mesh', dest='target_mesh', type=str, action='store', required=True,
                        help='Input ply target mesh filepath')
    parser.add_argument('-o', '--output', dest='output', type=str, action='store', required=True,
                        help='Output grouped json file')
    parser.add_argument('--corres', dest='corres', type=str, action='store', required=False,
                        help='Input picked corres points file')
    parser.add_argument('--icp_type', type=str, action='store', required=False,
                        default='color',
                        help='ICP method type, point2point, point2plane or color')
    parser.add_argument('--voxel_len', type=float, action='store', required=False,
                        default=0.1,
                        help='Downsample voxel length')
    parser.add_argument('--width', type=int, action='store', required=False,
                        default=640,
                        help='Visualization image width')
    parser.add_argument('--height', type=int, action='store', required=False,
                        default=480,
                        help='Visualization image height')
    parser.add_argument('--normal_estimation_radius', type=int, action='store', required=False,
                        default=3,
                        help='Normal estimation radius, radius = normal_estimation_radius * voxel_len')
    parser.add_argument('--normal_estimation_knn', type=int, action='store', required=False,
                        default=40,
                        help='Normal estimation maximum neighbors will be searched')
    parser.add_argument('--max_correspondence_distance', type=float, action='store', required=False,
                        default=1.1,
                        help='Max correspondence points pair distance, dist_thresh = max_correspondence_distance * voxel_len')
    parser.add_argument('--fpfh_feature_radius', type=float, action='store', required=False,
                        default=5.0,
                        help='Fpfh feature radius, radius = fpfh_feature_radius * voxel_len')
    parser.add_argument('--fpfh_feature_knn', type=int, action='store', required=False,
                        default=100,
                        help='Fpfh features computation maximum neighbors will be searched')
    parser.add_argument('--fpfh_max_distance', type=float, action='store', required=False,
                        default=1.1,
                        help='FPFH max correspondence points pair distance, dist_thresh = max_correspondence_distance * voxel_len')
    parser.add_argument('--voxel_length_pyramid', nargs='+', action='store', required=False,
                        default=[1, 4, 8],
                        help='Voxel length pyramid in multiscale icp, voxel_length = voxel_len / pyramid')
    parser.add_argument('--max_iter_pyramid', nargs='+', action='store', required=False,
                        default=[200, 150, 100],
                        help='Max iterations in multiscale icp')
    parser.add_argument('--pick_points', action='store_true',
                        help='Mannually select points to compute init transformation')
    args = parser.parse_args()

    params = {}
    params['icp_type'] = args.icp_type.upper()
    params['voxel_len'] = args.voxel_len
    params['width'] = args.width
    params['height'] = args.height
    params['normal_estimation_radius'] = args.normal_estimation_radius
    params['normal_estimation_knn'] = args.normal_estimation_knn
    params['max_correspondence_distance'] = args.max_correspondence_distance
    params['fpfh_feature_radius'] = args.fpfh_feature_radius
    params['fpfh_feature_knn'] = args.fpfh_feature_knn
    params['fpfh_max_distance'] = args.fpfh_max_distance
    params['voxel_length_pyramid'] = args.voxel_length_pyramid
    params['max_iter_pyramid'] = args.max_iter_pyramid
    params['pick_points'] = args.pick_points
    if args.corres:
        params['corres'] = args.corres
    output = align_pairs(args.source_id, args.target_id, args.source_mesh, args.target_mesh, params, args.output)
    
    if output:
        io.write_json(output, args.output)
        log.info(f'alignment result saved to {args.output}')
