from plyfile import PlyData, PlyElement
import open3d as o3d
from pyobb.obb import OBB
import numpy as np
import os
from scipy.spatial import ConvexHull, convex_hull_plot_2d
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
import argparse
import utils

def obb_calc(filename, gravity=np.array((0.0,1.0,0.0)), align_axis=np.array((0.0,0.0,-1.0))):
    o3d_mesh = o3d.io.read_triangle_mesh(filename)
    points = np.asarray(o3d_mesh.vertices)

    obb_center, obb_size, trans_inv = gravity_aligned_mobb(points, gravity, align_axis)
    obb = o3d.geometry.OrientedBoundingBox(obb_center, trans_inv, obb_size)
    
    return obb

def gravity_aligned_mobb(points, gravity, align_axis):
    def from2vectors(gravity, axis=align_axis):
        gravity = gravity/np.linalg.norm(gravity)
        axis = axis/np.linalg.norm(axis)
        vec = np.cross(gravity, axis)
        rot = np.arccos(np.dot(gravity, axis))
        r = R.from_rotvec(rot * vec)

        return r.as_matrix()

    # trigonometry, law of sines: a/sin(A) = b/sin(B)
    def intersect_lines(s0, d0, s1 ,d1):
        """
        s0, s1: 2D coordinates of a point
        d0, d1: direction vector determines the direction a line
        """
        sin_a = np.cross(d0, d1)
        vec_s = s1-s0
        t = np.cross(vec_s, d1)/sin_a

        return s0 + t*d0

    def mobb_area(left_start, left_dir, right_start, right_dir,
            top_start, top_dir, bottom_start, bottom_dir):
        upper_left = intersect_lines(left_start, left_dir, top_start, top_dir)
        upper_right = intersect_lines(right_start, right_dir, top_start, top_dir)
        bottom_left = intersect_lines(bottom_start, bottom_dir, left_start, left_dir)

        return np.linalg.norm(upper_left-upper_right) * np.linalg.norm(upper_left-bottom_left)
    
    align_gravity = from2vectors(gravity, align_axis)

    tmp_points = np.matmul(align_gravity, points.transpose()).transpose()
    points_2d = tmp_points[:, 0:2]
    hull = ConvexHull(points_2d)

    # plot conver hull
    # print(len(hull.vertices))
    # plt.plot(points_2d[:,0], points_2d[:,1], '.')
    # plt.plot(points_2d[hull.vertices,0], points_2d[hull.vertices,1], 'r--', lw=2)
    # plt.plot(points_2d[(hull.vertices[-1], hull.vertices[0]),0], points_2d[(hull.vertices[-1], hull.vertices[0]),1], 'r--', lw=2)
    # plt.plot(points_2d[hull.vertices[0],0], points_2d[hull.vertices[0],1], 'ro')
    # plt.show()

    assert len(hull.vertices) > 0, 'convex hull vertices number must be positive'
    
    # the vertices are in counterclockwise order
    hull_points = points_2d[hull.vertices]
    
    edge_dirs = np.roll(hull_points, 1, axis=0) - hull_points
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

    min_area = np.finfo(np.float).max
    best_bottom_dir = np.array((np.nan, np.nan))

    ortho = lambda v: np.array((v[1], -v[0]))

    for i in range((len(hull.vertices))):
        angles = [np.arccos(np.dot(left_dir, edge_dirs[left_idx])),
            np.arccos(np.dot(right_dir, edge_dirs[right_idx])),
            np.arccos(np.dot(top_dir, edge_dirs[top_idx])),
            np.arccos(np.dot(bottom_dir, edge_dirs[bottom_idx]))]
        angles = np.asarray(angles)

        best_line = np.argmin(angles)
        min_angle = angles[best_line]

        if best_line == 0:
            left_dir = edge_dirs[left_idx]
            right_dir = -left_dir
            top_dir = ortho(left_dir)
            bottom_dir = -top_dir
            left_idx = (left_idx+1)%len(hull.vertices)
        elif best_line == 1:
            right_dir = edge_dirs[right_idx]
            left_dir = -right_dir
            top_dir = ortho(left_dir)
            bottom_dir = -top_dir
            right_idx = (right_idx+1)%len(hull.vertices)
        elif best_line == 2:
            top_dir = edge_dirs[top_idx]
            bottom_dir = -top_dir
            left_dir = ortho(bottom_dir)
            right_dir = -left_dir
            top_idx = (top_idx+1)%len(hull.vertices)
        elif best_line == 3:
            bottom_dir = edge_dirs[bottom_idx]
            top_dir = -bottom_dir
            left_dir = ortho(bottom_dir)
            right_dir = -left_dir
            bottom_idx = (bottom_idx+1)%len(hull.vertices)
        else:
            assert False
        
        area = mobb_area(hull_points[left_idx], left_dir, hull_points[right_idx], right_dir,
            hull_points[top_idx], top_dir, hull_points[bottom_idx], bottom_dir)
        
        if area < min_area:
            min_area = area
            best_bottom_dir = bottom_dir
    
    trans_w2b = np.matmul(from2vectors(np.array((best_bottom_dir[0], best_bottom_dir[1], 0.0)),
        np.array((1.0,0.0,0.0))), align_gravity)
    aligned_points = np.matmul(trans_w2b, points.transpose()).transpose()
    
    min_pt = np.amin(aligned_points, axis=0)
    max_pt = np.amax(aligned_points, axis=0)

    center = (min_pt+max_pt)/2.0

    trans_inv = np.linalg.inv(trans_w2b)
    obb_center = np.matmul(trans_inv, center)
    obb_size = max_pt-min_pt

    return obb_center, obb_size, trans_inv
    

def o3d_render(filename, output, win_width=640, obb=None, show_obb=False):
    o3d_mesh = o3d.io.read_triangle_mesh(filename)

    if obb is None and show_obb:
        obb = o3d_mesh.get_oriented_bounding_box()

    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name='Result', width=win_width, height=int(192/256*win_width), visible=True)
    if show_obb:
        vis.add_geometry(obb)
    vis.add_geometry(o3d_mesh)
    # vis.run()
    vis.capture_screen_image(filename=output, do_render=True)
    vis.destroy_window()
    

def configure(args):
    if not utils.file_exist(args.input, '.ply'):
        utils.print_e(f'Input file {args.input} not exists')
        return False

    if not utils.folder_exist(os.path.dirname(args.output)):
        utils.print_e(f'Cannot open file {args.output}')
        return False

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Render thumbnail for result ply mesh!')
    parser.add_argument('-i', '--input', dest='input', type=str, action='store', required=True,
                        help='Input mesh file')
    parser.add_argument('-w', '--width', dest='width', default=200, type=int, action='store', required=False,
                        help='Rendered image width')
    parser.add_argument('-obb', '--show_obb', dest='show_obb', default=False, action='store_true',
                        required=False, help='Show oriented bounding box')
    parser.add_argument('-o', '--output', dest='output', type=str, action='store', required=True,
                        help='Output rendered image')
    
    args = parser.parse_args()

    if not configure(args):
        exit(0)
    
    obb = None
    if args.show_obb:
        obb = obb_calc(args.input, np.array((0,1,0)), np.array((0,0,-1)))
    o3d_render(args.input, args.output, win_width=args.width, obb=obb, show_obb=args.show_obb)