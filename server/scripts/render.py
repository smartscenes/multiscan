import argparse
import os
import logging
import trimesh
import pyrender
import numpy as np
import cv2

from pyrender.constants import (DEFAULT_SCENE_SCALE,
                                DEFAULT_Z_FAR, DEFAULT_Z_NEAR)

from multiscan.utils import io
from multiscan.meshproc import TriMesh

os.environ['PYOPENGL_PLATFORM'] = 'egl'

def compute_initial_camera_pose(scene):
        centroid = scene.centroid
        scale = scene.scale
        if scale == 0.0:
            scale = DEFAULT_SCENE_SCALE

        cp = np.eye(4)
        hfov = np.pi / 4.0
        dist = scale / (1.0 * np.tan(hfov))
        cp[:3, 3] = dist * np.array([0.0, 0.0, 1.0]) + centroid

        return cp

# TODO: allow pass camera pose
def render(input, output, width, height, show_obb=False, paint_uniform_color=False):
    if os.path.splitext(input)[-1] == '.ply':
        mesh = TriMesh(input)
        # transform_output = os.path.splitext(input)[0]
        # mesh.align_mesh(transform_output+'-align-transform.json')
        mesh.o3d_render(output=output, win_width=width, win_height=height, show_obb=show_obb, show_frame=False, 
                        paint_uniform_color=paint_uniform_color, show_window=False)
    elif os.path.splitext(input)[-1] == '.obj':
        raw_trimesh = trimesh.load(input, force='scene')
        scene = pyrender.Scene.from_trimesh_scene(raw_trimesh)
        scene.ambient_light = [1.0, 1.0, 1.0]

        window_ratio = height / width

        renderer = pyrender.OffscreenRenderer(viewport_width=1080 * 2, viewport_height=int(window_ratio * 1080 * 2))
        # set up camera
        zfar = max(scene.scale * 10.0, DEFAULT_Z_FAR)
        if scene.scale == 0:
            znear = DEFAULT_Z_NEAR
        else:
            znear = min(scene.scale / 10.0, DEFAULT_Z_NEAR)
        cam = pyrender.PerspectiveCamera(yfov=np.pi / 4.0, znear=znear, zfar=zfar)
        cam_pose = compute_initial_camera_pose(scene)
        cam_node = pyrender.Node(camera=cam, matrix=cam_pose)
        scene.add_node(cam_node)

        color, _ = renderer.render(scene)
        # if the window is small, there will be artifacts in the renderered result
        color = cv2.resize(color, (width, height))
        color = cv2.cvtColor(color, cv2.COLOR_RGB2BGR)
        cv2.imwrite(output, color)



def configure(args):
    if not io.file_exist(args.input, '.ply') and not io.file_exist(args.input, '.obj'):
        logging.error(f'Input file {args.input} not exists')
        return False

    if not io.folder_exist(os.path.dirname(args.output)):
        logging.error(f'Cannot open file {args.output}')
        return False

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Render thumbnail for result ply mesh!')
    parser.add_argument('-i', '--input', dest='input', type=str, action='store', required=True,
                        help='Input mesh file')
    parser.add_argument('--width', dest='width', default=640, type=int, action='store', required=False,
                        help='Rendered image width')
    parser.add_argument('--height', dest='height', default=480, type=int, action='store', required=False,
                        help='Rendered image height')
    parser.add_argument('-obb', '--show_obb', dest='show_obb', default=False, action='store_true',
                        required=False, help='Show oriented bounding box')
    parser.add_argument('--paint_uniform_color', default=False, action='store_true',
                        required=False, help='Paint ply mesh with uniform color')
    parser.add_argument('-o', '--output', dest='output', type=str, action='store', required=True,
                        help='Output rendered image')

    args = parser.parse_args()

    if not configure(args):
        exit(0)

    render(args.input, args.output, args.width, args.height, args.show_obb, args.paint_uniform_color)
