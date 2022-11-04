import argparse
import json
import os
import logging

import cv2
import numpy as np
import pymeshlab
import trimesh
import pyrender

from pyrender.constants import (DEFAULT_SCENE_SCALE,
                                DEFAULT_Z_FAR, DEFAULT_Z_NEAR)

from multiscan.utils import io

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


def segm_render(input_mesh, input_segs, output_dir, output_mesh=True, width=640, height=480):
    ms = pymeshlab.MeshSet()
    ms.load_new_mesh(input_mesh)

    mesh = ms.current_mesh()
    np_vertices = mesh.vertex_matrix()
    np_faces = mesh.face_matrix()

    num_vertices = np.shape(np_vertices)[0]
    num_faces = np.shape(np_faces)[0]

    with open(input_segs, 'r') as f:
        data = json.load(f)
        levels = data['hierarchies'][0]['levels']
    
    for i, level in enumerate(levels):
        name = data['segmentation'][i]['name']
        element_type = data['segmentation'][i]['elementType']
        seg = data['segmentation'][i]['index']
        val, idx = np.unique(seg, return_index=True)
        r = np.random.choice(255, len(val))
        g = np.random.choice(255, len(val))
        b = np.random.choice(255, len(val))

        face_based = False if element_type == 'vertices' else True
        num_elements = num_faces if face_based else num_vertices
        
        assert len(np.asarray(seg)) == num_elements
    
        id2color = {}
        for i in range(len(val)):
            id2color[str(val[i])] = np.array((r[i], g[i], b[i], 255)).astype(np.uint8)

        colors = []
        for i in range(num_elements):
            colors.append(id2color[str(seg[i])])

        tm = trimesh.Trimesh(vertices=np_vertices, faces=np_faces, process=False)
        if face_based:
            tm.visual.face_colors = colors
        else:
            tm.visual.vertex_colors = colors
        pr_mesh = pyrender.Mesh.from_trimesh(tm, smooth=(not face_based))
        scene = pyrender.Scene()
        scene.ambient_light = [1.0, 1.0, 1.0]
        scene.add(pr_mesh)
        
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
        renderer.delete()

        basename = os.path.splitext(os.path.basename(input_segs))[0] + '-' + name
        out_file =basename +'.png'
        if output_mesh:
            out_meshfile = basename +'.ply'
            tm.export(os.path.join(output_dir, out_meshfile), file_type='ply')
        cv2.imwrite(os.path.join(output_dir, out_file), color)


def configure(args):
    if not io.file_exist(args.input, '.ply') and not io.file_exist(args.input, '.obj'):
        logging.error(f'Input file {args.input} not exists')
        return False

    if not io.file_exist(args.segs, '.json'):
        logging.error(f'Input segmentation file {args.input} not exists')
        return False

    if args.output is None:
        args.output = os.path.dirname(args.input)

    if not io.folder_exist(args.output):
        logging.error(f'Cannot create file in folder {args.output}')
        return False

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Decode depth stream!')
    parser.add_argument('-i', '--input', dest='input', type=str, action='store', required=True,
                        help='Input mesh ply file')
    parser.add_argument('-segs', '--segs', dest='segs', type=str, action='store', required=True,
                        help='Input mesh segmentation json file')
    parser.add_argument('--width', dest='width', type=int, action='store', required=False, default=640,
                        help='width of output visualization image')
    parser.add_argument('--height', dest='height', type=int, action='store', required=False, default=480,
                        help='height of output visualization image')
    parser.add_argument('--output_mesh', dest='output_mesh', default=False, action='store_true', required=False,
                        help='Output colored segmentation visualization mesh')
    parser.add_argument('-o', '--output', dest='output', type=str, action='store', required=False,
                        help='Output directory of the segmentation visualization figure')

    args = parser.parse_args()

    if not configure(args):
        exit(0)

    segm_render(args.input, args.segs, args.output, args.output_mesh, args.width, args.height)
