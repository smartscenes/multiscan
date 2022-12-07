import logging

import matplotlib.pyplot as plt
import numpy as np
import open3d as o3d
import pymeshlab
from scipy.spatial import ConvexHull

from multiscan.utils import io
from multiscan.meshproc import rotation_from2vectors, intersect_lines


class TriMesh:
    def __init__(self, mesh):
        if mesh and isinstance(mesh, str) and io.file_exist(mesh):
            self.o3d_mesh = o3d.io.read_triangle_mesh(mesh)
        elif isinstance(mesh, o3d.geometry.TriangleMesh):
            self.o3d_mesh = mesh
        else:
            raise f'{mesh} is not a open3d triangle mesh instance'
        self.obb = None

        self.logger = logging.getLogger('TriMesh logger')
        self.logger.setLevel(logging.INFO)

        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.INFO)

        # create formatter
        self.formatter = logging.Formatter('%(asctime)-15s [%(levelname)s] %(message)s')
        self.ch.setFormatter(self.formatter)
        self.logger.addHandler(self.ch)

    def obb_calc(self, aligned=True, gravity=np.array((0.0, 1.0, 0.0)), align_axis=np.array((0.0, 0.0, -1.0))):
        if aligned:
            obb_center, obb_size, trans_inv = self.__gravity_aligned_mobb(gravity, align_axis)
            self.obb = o3d.geometry.OrientedBoundingBox(obb_center, trans_inv, obb_size)
        else:
            self.obb = self.o3d_mesh.get_oriented_bounding_box()
        return self.obb

    def align_mesh(self, transform_output=None):
        if not self.obb:
            self.obb_calc()
        rotation = self.obb.R.copy()
        center = self.obb.center.copy()
        transform_mat = np.diag([1.0, 1.0, 1.0, 1.0])
        rotation_mat = transform_mat.copy()
        translation_mat = transform_mat.copy()
        rotation_mat[0:3, 0:3] = rotation
        translation_mat[0:3, 3] = center
        transform_mat = np.matmul(rotation_mat, transform_mat)
        transform_mat = np.matmul(translation_mat, transform_mat)
        trans_info = {'rotation': rotation.flatten(order='F').tolist(),
                      'center': center.tolist(), 'transform': transform_mat.flatten(order='F').tolist()}
        if transform_output:
            io.write_json(trans_info, transform_output)
        self.o3d_mesh.transform(np.linalg.inv(transform_mat))
        self.obb.translate(-center)
        self.obb.rotate(rotation.transpose())
        return transform_mat

    def align_back(self, filename):
        data = io.read_json(filename)

        transform_mat = np.asarray(data['transform']).reshape((4, 4), order='F')
        rotation = np.asarray(data['rotation']).reshape((3, 3), order='F')
        center = np.asarray(data['center'])
        if self.obb:
            self.obb.rotate(rotation, center)
        if self.o3d_mesh:
            self.o3d_mesh.transform(transform_mat)

    def __gravity_aligned_mobb(self, gravity, align_axis, nb_neighbors=20, std_ratio=3.0, debug=False):
        pcd = o3d.geometry.PointCloud(self.o3d_mesh.vertices)
        pcd, _ = pcd.remove_statistical_outlier(nb_neighbors, std_ratio)
        points = np.asarray(pcd.points)

        def mobb_area(left_start, left_dir, right_start, right_dir,
                      top_start, top_dir, bottom_start, bottom_dir):
            upper_left = intersect_lines(left_start, left_dir, top_start, top_dir)
            upper_right = intersect_lines(right_start, right_dir, top_start, top_dir)
            bottom_left = intersect_lines(bottom_start, bottom_dir, left_start, left_dir)

            return np.linalg.norm(upper_left - upper_right) * np.linalg.norm(upper_left - bottom_left)

        align_gravity = rotation_from2vectors(gravity, align_axis)

        tmp_points = np.matmul(align_gravity, points.transpose()).transpose()
        points_2d = tmp_points[:, 0:2]
        hull = ConvexHull(points_2d)

        # plot conver hull
        if debug:
            self.logger.debug(len(hull.vertices))
            fig = plt.figure(figsize=(5, 5))
            ax = fig.add_subplot(111)
            plt.plot(points_2d[:, 0], points_2d[:, 1], '.')
            plt.plot(points_2d[hull.vertices, 0],
                     points_2d[hull.vertices, 1], 'r--', lw=4)
            plt.plot(points_2d[(hull.vertices[-1], hull.vertices[0]), 0],
                     points_2d[(hull.vertices[-1], hull.vertices[0]), 1], 'r--', lw=4)
            plt.plot(points_2d[hull.vertices[:], 0], points_2d[hull.vertices[:], 1],
                     marker='o', markersize=7, color="red")
            ax.set_aspect('equal', adjustable='box')
        assert len(hull.vertices) > 0, 'convex hull vertices number must be positive'

        # the vertices are in counterclockwise order
        hull_points = points_2d[hull.vertices]

        edge_dirs = np.roll(hull_points, -1, axis=0) - hull_points
        edge_norm = np.linalg.norm(edge_dirs, axis=1)
        edge_dirs /= edge_norm[:, None]

        min_idx = np.argmin(hull_points, axis=0)
        max_idx = np.argmax(hull_points, axis=0)
        min_pt = np.array((hull_points[min_idx[0]][0], hull_points[min_idx[1]][1]))
        max_pt = np.array((hull_points[max_idx[0]][0], hull_points[max_idx[1]][1]))

        left_idx = min_idx[0]
        right_idx = max_idx[0]
        top_idx = max_idx[1]
        bottom_idx = min_idx[1]

        left_dir = np.array((0, -1))
        right_dir = np.array((0, 1))
        top_dir = np.array((-1, 0))
        bottom_dir = np.array((1, 0))

        if debug:
            plt.plot(hull_points[bottom_idx][0], hull_points[bottom_idx][1],
                     marker='o', markersize=14, color="r")
            plt.axline((hull_points[bottom_idx][0], hull_points[bottom_idx][1]), (
                hull_points[bottom_idx][0] + bottom_dir[0], hull_points[bottom_idx][1] + bottom_dir[1]))
            plt.plot(hull_points[left_idx][0], hull_points[left_idx][1],
                     marker='o', markersize=14, color="r")
            plt.axline((hull_points[left_idx][0], hull_points[left_idx][1]), (
                hull_points[left_idx][0] + left_dir[0], hull_points[left_idx][1] + left_dir[1]))
            plt.plot(hull_points[right_idx][0], hull_points[right_idx][1],
                     marker='o', markersize=14, color="r")
            plt.axline((hull_points[right_idx][0], hull_points[right_idx][1]), (
                hull_points[right_idx][0] + right_dir[0], hull_points[right_idx][1] + right_dir[1]))
            plt.plot(hull_points[top_idx][0], hull_points[top_idx][1],
                     marker='o', markersize=14, color="r")
            plt.axline((hull_points[top_idx][0], hull_points[top_idx][1]), (
                hull_points[top_idx][0] + top_dir[0], hull_points[top_idx][1] + top_dir[1]))

        min_area = np.finfo(np.float).max
        best_bottom_dir = np.array((np.nan, np.nan))
        best_bottom_idx = -1
        best_left_dir = np.array((np.nan, np.nan))
        best_left_idx = -1
        best_top_dir = np.array((np.nan, np.nan))
        best_top_idx = -1
        best_right_dir = np.array((np.nan, np.nan))
        best_right_idx = -1

        def ortho(v):
            return np.array([v[1], -v[0]])

        for i in range((len(hull.vertices))):
            angles = [np.arccos(np.clip(np.dot(left_dir, edge_dirs[left_idx]), -1.0, 1.0)),
                      np.arccos(np.clip(np.dot(right_dir, edge_dirs[right_idx]), -1.0, 1.0)),
                      np.arccos(np.clip(np.dot(top_dir, edge_dirs[top_idx]), -1.0, 1.0)),
                      np.arccos(np.clip(np.dot(bottom_dir, edge_dirs[bottom_idx]), -1.0, 1.0))]
            angles = np.asarray(angles)

            best_line = np.argmin(angles)
            min_angle = angles[best_line]

            if best_line == 0:
                left_dir = edge_dirs[left_idx]
                right_dir = -left_dir
                top_dir = ortho(left_dir)
                bottom_dir = -top_dir
                left_idx = (left_idx + 1) % len(hull.vertices)
            elif best_line == 1:
                right_dir = edge_dirs[right_idx]
                left_dir = -right_dir
                top_dir = ortho(left_dir)
                bottom_dir = -top_dir
                right_idx = (right_idx + 1) % len(hull.vertices)
            elif best_line == 2:
                top_dir = edge_dirs[top_idx]
                bottom_dir = -top_dir
                left_dir = ortho(bottom_dir)
                right_dir = -left_dir
                top_idx = (top_idx + 1) % len(hull.vertices)
            elif best_line == 3:
                bottom_dir = edge_dirs[bottom_idx]
                top_dir = -bottom_dir
                left_dir = ortho(bottom_dir)
                right_dir = -left_dir
                bottom_idx = (bottom_idx + 1) % len(hull.vertices)
            else:
                assert False

            area = mobb_area(hull_points[left_idx], left_dir, hull_points[right_idx], right_dir,
                             hull_points[top_idx], top_dir, hull_points[bottom_idx], bottom_dir)

            if area < min_area:
                min_area = area
                best_bottom_dir = bottom_dir
                best_bottom_idx = bottom_idx
                best_left_dir = left_dir
                best_left_idx = left_idx
                best_right_dir = right_dir
                best_right_idx = right_idx
                best_top_dir = top_dir
                best_top_idx = top_idx

        p_bl = intersect_lines(
            hull_points[best_bottom_idx], best_bottom_dir, hull_points[best_left_idx], best_left_dir)
        p_br = intersect_lines(
            hull_points[best_bottom_idx], best_bottom_dir, hull_points[best_right_idx], best_right_dir)
        p_tl = intersect_lines(
            hull_points[best_left_idx], best_left_dir, hull_points[best_top_idx], best_top_dir)

        len_b = np.linalg.norm(p_bl - p_br)
        len_l = np.linalg.norm(p_bl - p_tl)

        if len_b < len_l:
            vec = best_bottom_dir / np.linalg.norm(best_bottom_dir)
        else:
            vec = best_left_dir / np.linalg.norm(best_left_dir)
            self.logger.debug(vec)
        vec = np.concatenate([vec, [0]])
        if debug:
            plt.axline((hull_points[best_bottom_idx][0], hull_points[best_bottom_idx][1]), (
                hull_points[best_bottom_idx][0] + best_bottom_dir[0],
                hull_points[best_bottom_idx][1] + best_bottom_dir[1]), color="m", lw=6)
            plt.axline((hull_points[best_left_idx][0], hull_points[best_left_idx][1]), (
                hull_points[best_left_idx][0] + best_left_dir[0], hull_points[best_left_idx][1] + best_left_dir[1]),
                       color="m", lw=6)
            plt.axline((hull_points[best_right_idx][0], hull_points[best_right_idx][1]), (
                hull_points[best_right_idx][0] + best_right_dir[0], hull_points[best_right_idx][1] + best_right_dir[1]),
                       color="m", lw=6)
            plt.axline((hull_points[best_top_idx][0], hull_points[best_top_idx][1]), (
                hull_points[best_top_idx][0] + best_top_dir[0], hull_points[best_top_idx][1] + best_top_dir[1]),
                       color="m", lw=6)

            plt.plot(hull_points[best_bottom_idx][0], hull_points[best_bottom_idx][1],
                     marker='o', markersize=21, color="g")
            plt.plot(hull_points[best_left_idx][0], hull_points[best_left_idx][1],
                     marker='o', markersize=21, color="g")
            plt.plot(hull_points[best_right_idx][0], hull_points[best_right_idx][1],
                     marker='o', markersize=21, color="g")
            plt.plot(hull_points[best_top_idx][0], hull_points[best_top_idx][1],
                     marker='o', markersize=21, color="g")
            plt.show()

        third_t = np.array([np.cross(-vec, align_axis), -vec, align_axis])
        trans_w2b = np.matmul(third_t, align_gravity)
        aligned_points = np.matmul(trans_w2b, points.transpose()).transpose()

        min_pt = np.amin(aligned_points, axis=0)
        max_pt = np.amax(aligned_points, axis=0)

        center = (min_pt + max_pt) / 2.0

        trans_inv = np.linalg.inv(trans_w2b)
        obb_center = np.matmul(trans_inv, center)
        obb_size = max_pt - min_pt

        return obb_center, obb_size, trans_inv

    def o3d_render(self, output=None, win_width=640, win_height=480, show_obb=False, show_frame=False,
                   paint_uniform_color=False, show_window=False):
        vis = o3d.visualization.Visualizer()
        vis.create_window(window_name='TriMesh', width=win_width, height=win_height, visible=True)
        if show_obb and self.obb:
            vis.add_geometry(self.obb)
        if paint_uniform_color:
            self.o3d_mesh.paint_uniform_color(np.array([0.65, 0.65, 0.65]))
            self.o3d_mesh.compute_vertex_normals()
        vis.add_geometry(self.o3d_mesh)
        if show_frame:
            vis.add_geometry(o3d.geometry.TriangleMesh.create_coordinate_frame())
        if output:
            vis.capture_screen_image(filename=output, do_render=True)
        if show_window:
            vis.run()
            vis.destroy_window()

    @staticmethod
    def cleanup_mesh(input_file, min_iso_face_num=50, output_file=None, log=None):
        if output_file is None:
            output_file = input_file
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(input_file)
        if log:
            log.debug(f"Number of vertices loaded: {ms.current_mesh().vertex_number()}")
        ms.remove_duplicate_faces()
        ms.remove_duplicate_vertices()
        ms.remove_zero_area_faces()
        ms.repair_non_manifold_edges_by_removing_faces()
        ms.remove_isolated_pieces_wrt_face_num(mincomponentsize=min_iso_face_num)
        # convert texture mesh to ply mesh with vertex colors
        if io.file_extension(input_file) == '.obj' and io.file_extension(output_file) == '.ply':
            ms.transfer_color_texture_to_vertex()
            ms.save_current_mesh(output_file, save_vertex_normal=True,
                                 save_face_color=False, save_wedge_texcoord=False)
        else:
            ms.re_compute_vertex_normals(weightmode=0)
            ms.save_current_mesh(output_file, save_vertex_normal=True)
        if log:
            log.debug(f"Number of vertices after postprocessing: {ms.current_mesh().vertex_number()}")

    @staticmethod
    def transfer_color_texture_to_vertex(input_file, output_file):
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(input_file)
        # convert texture mesh to ply mesh with vertex colors
        if io.file_extension(input_file) == '.obj' and io.file_extension(output_file) == '.ply':
            ms.transfer_color_texture_to_vertex()
            ms.save_current_mesh(output_file, save_vertex_normal=True,
                                 save_face_color=False, save_wedge_texcoord=False)