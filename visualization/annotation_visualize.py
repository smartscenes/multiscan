import os
import re
import requests
import random
import numpy as np
import pyrender
import hashlib
from urllib.parse import urljoin
import trimesh
import logging
import matplotlib
from PIL import Image
from matplotlib import cm
import pandas as pd
from plyfile import PlyData
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from scipy.spatial.transform import Rotation as R

import matplotlib.colors as mc
import colorsys
from io import BytesIO

import hydra
from omegaconf import DictConfig

from multiscan.utils import io
from visualization import Visualizer

log = logging.getLogger(__name__)

class ArrowColor:
    def _tabcolor_by_index(index, cmap_name='tab20'):
        return np.asarray(list(cm.get_cmap(cmap_name)(index)))

    BLUE_DARK = _tabcolor_by_index(0)
    BLUE_LIGHT = _tabcolor_by_index(1)
    ORANGE_DARK = _tabcolor_by_index(2)
    ORANGE_LIGHT = _tabcolor_by_index(3)
    GREEN_DARK = _tabcolor_by_index(4)
    GREEN_LIGHT = _tabcolor_by_index(5)
    RED_DARK = _tabcolor_by_index(6)
    RED_LIGHT = _tabcolor_by_index(7)
    PURPLE_DARK = _tabcolor_by_index(8)
    PURPLE_LIGHT = _tabcolor_by_index(9)

def lighten_color(color, amount=0.8, alpha=0.7):
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    rgb = np.asarray(colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2]))
    return np.concatenate((rgb, [alpha]))

class AnnotationVisualize:
    def __init__(self, cfg, input_dir):
        self.cfg = cfg
        self._arrow_ply = PlyData.read(BytesIO(requests.get(urljoin(cfg.arrow_ply_gist_url, 'arrow.ply')).content))
        self._arrow_head_ply = PlyData.read(BytesIO(requests.get(urljoin(cfg.arrow_ply_gist_url, 'arrow_head.ply')).content))
        self._head_body_ratio = 0.25

        self.input_dir = input_dir
        self.scan_id = self.get_scan_id(input_dir)
        
        self.visualizer = Visualizer()
        self.seed = self.set_seed()
        self.cmap = matplotlib.colors.ListedColormap(np.random.rand(256, 3))
        self._z_axis = [0, 0, 1+1e-5]

        self.plydata = self._get_plydata()
        
        self.alignment = self._get_alignment()
        self.semseg_df = self.semseg_triangles()
        self.annotations = self._get_annotations()
        self.object_semantic_id_map = self._get_object_semantic_id_map()

        self.world_up = np.array([0, 0, 1])
        self.hfov = np.pi/4.0
        self.scene_centroid = np.array([0, 0, 0])
        self.scene_scale = 1.0

    def update_scan(self, input_dir):
        self.input_dir = input_dir
        self.scan_id = self.get_scan_id(input_dir)

        self.plydata = self._get_plydata()

        self.alignment = self._get_alignment()
        self.semseg_df = self.semseg_triangles()
        self.annotations = self._get_annotations()
        self.object_semantic_id_map = self._get_object_semantic_id_map()

    @staticmethod
    def get_scan_id(key):
        return re.findall(r"scene\_[0-9]{5}\_[0-9]{2}", key)[0]

    @staticmethod
    def set_seed(seed=4):
        np.random.seed(seed)
        random.seed(seed)
        return seed

    def _get_annotations(self):
        return io.read_json(os.path.join(self.input_dir, f'{self.scan_id}.annotations.json'))

    def _get_alignment(self):
        ref_align = io.read_json(os.path.join(self.input_dir, f'{self.scan_id}.align.json')).get('reference_scan_alignment', None)
        if ref_align is not None:
            alignment = np.asarray(ref_align['transformation']).reshape((4, 4), order='F')
        else:
            alignment = np.eye(4)
        return alignment

    def _get_plydata(self):
        return PlyData.read(os.path.join(self.input_dir, f'{self.scan_id}.ply'))

    def _construct_ply_mesh(self):
        x = np.asarray(self.plydata['vertex']['x'])
        y = np.asarray(self.plydata['vertex']['y'])
        z = np.asarray(self.plydata['vertex']['z'])
        nx = np.asarray(self.plydata['vertex']['nx'])
        ny = np.asarray(self.plydata['vertex']['ny'])
        nz = np.asarray(self.plydata['vertex']['nz'])
        red = self.plydata['vertex']['red'].astype('float64') / 255.
        green = self.plydata['vertex']['green'].astype('float64') / 255.
        blue = self.plydata['vertex']['blue'].astype('float64') / 255.
        
        vertices = np.column_stack((x, y, z))
        vertex_normals = np.column_stack((nx, ny, nz))
        vertex_colors = np.column_stack((red, green, blue))
        triangles = np.vstack(self.plydata['face'].data['vertex_indices'])
        return vertices, vertex_colors, vertex_normals, triangles

    def semseg_triangles(self):
        object_ids = self.plydata['face'].data['objectId']
        part_ids = self.plydata['face'].data['partId']
        return pd.DataFrame({'objectId': object_ids, 'partId': part_ids})

    def object_triangles(self, object_id):
        condition1 = self.semseg_df['objectId'] == object_id
        return self.semseg_df[condition1].index.values

    def part_triangles(self, object_id, part_id):
        condition1 = self.semseg_df['objectId'] == object_id
        condition2 = self.semseg_df['partId'] == part_id
        return self.semseg_df[condition1 & condition2].index.values

    def draw_arrow(self, origin, axis, head_color, body_color, radius=0.01, length=0.5):
        head_length = length * self._head_body_ratio
        body_length = length - head_length
        head_transformation = np.eye(4)
        head_transformation[:3, 3] += [0, 0, body_length / 2.0]
        head = trimesh.creation.cone(3 * radius, head_length, sections=40, transform=head_transformation)
        head.visual.vertex_colors = head_color
        body = trimesh.creation.cylinder(radius, body_length, sections=40)
        body.visual.vertex_colors = body_color
        arrow = trimesh.util.concatenate([head, body])

        transformation = trimesh.geometry.align_vectors(self._z_axis, axis)
        transformation[:3, 3] += np.asarray(origin) + np.asarray(axis) * (1 - self._head_body_ratio) / 2 * length
        arrow.apply_transform(transformation)
        return arrow

    @staticmethod
    def plydata_to_trimesh(plydata, color):
        x = plydata['vertex']['x']
        y = plydata['vertex']['y']
        z = plydata['vertex']['z']
        vertices = np.column_stack((x, y, z))

        nx = plydata['vertex']['nx']
        ny = plydata['vertex']['ny']
        nz = plydata['vertex']['nz']
        vertex_normals = np.column_stack((nx, ny, nz))
        
        tri_data = plydata['face'].data['vertex_indices']
        triangles = np.vstack(tri_data)

        return trimesh.Trimesh(vertices, faces=triangles, vertex_normals=vertex_normals, vertex_colors=color)

    def rotation_arrow(self, origin, axis, head_color, body_color, length=0.5):
        transformation = trimesh.geometry.align_vectors(self._z_axis, axis)
        transformation[:3, 3] += np.asarray(origin) + np.asarray(axis) * (1 - self._head_body_ratio) / 2 * length

        arrow_head = self.plydata_to_trimesh(self._arrow_head_ply, head_color)
        arrow = self.plydata_to_trimesh(self._arrow_ply, body_color)
        scale = length * 0.1
        curling_arrow = trimesh.util.concatenate([arrow_head, arrow]).apply_transform(np.diag([scale, scale, scale, 1.0]))
        curling_arrow.apply_transform(transformation)
        
        arrow_radious = max(length * 0.02, 0.01)
        arrow = self.draw_arrow(origin, axis, head_color, body_color, radius=arrow_radious, length=length)

        sphere = trimesh.creation.icosphere(subdivisions=4, radius=3*arrow_radious)
        sphere.visual.vertex_colors = head_color
        sphere_transformation = np.eye(4)
        sphere_transformation[:3, 3] = [0, 0, (-length + length * self._head_body_ratio) / 2.0]
        sphere.apply_transform(sphere_transformation)
        sphere.apply_transform(transformation)

        rotation_arrow = trimesh.util.concatenate([curling_arrow, arrow, sphere])
        return rotation_arrow
        
    def translation_arrow(self, origin, axis, head_color, body_color, length=0.5):
        arrow_radious = max(length * 0.02, 0.01)
        translation_arrow = self.draw_arrow(origin, axis, head_color, body_color, radius=arrow_radious, length=length*1.5)
        return translation_arrow

    @staticmethod
    def mesh_background_face_colors(faces):
        face_colors = np.ones((faces.shape[0], 4)) * 0.3
        face_colors[:, 3] = 0.6
        return face_colors

    @staticmethod
    def string_to_hash_int(s, max_val=255):
        return int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16) % (max_val+1)

    @staticmethod
    def annotations_to_dataframe(annotations):
        objects = annotations['objects']
        parts = annotations['parts']

        df_list = []
        for obj in objects:
            object_id = obj['objectId']
            object_label = obj['label']
            part_ids = obj['partIds']
            for part_id in part_ids:
                part = parts[part_id-1]
                part_label = part['label']
                assert part_id == part['partId']
                df_row = pd.DataFrame(
                    [[object_id, part_id, object_label, part_label]],
                    columns=['objectId', 'partId', 'objectLabel', 'partLabel']
                )
                df_list.append(df_row)
        df = pd.concat(df_list)
        return df

    def _get_object_semantic_id_map(self):
        return pd.read_csv(os.path.join(self.cfg.object_semantic_label_map_csv))

    def object_semantic_id(self, object_label):
        df = self.object_semantic_id_map
        object_name = object_label.split('.')[0]
        semantic_id = df[df['objectName'] == object_name]['objectSemanticId']
        if len(semantic_id) > 0:
            return semantic_id.iat[0]
        else:
            return 0

    @staticmethod
    def mesh_from_face_colors(vertices, triangles, face_colors, transform=np.eye(4)):
        positions = vertices[triangles].reshape((3 * len(triangles), 3))
        colors = np.repeat(face_colors, 3, axis=0)
        primitive = pyrender.Primitive(positions=positions, color_0=colors, material=None, mode=4, poses=[transform])
        mesh = pyrender.Mesh([primitive])
        return mesh

    def textured_scene(self):
        textured_mesh_file = os.path.join(self.input_dir, 'textured_mesh', f'{self.scan_id}.obj')
        trimesh_scene = trimesh.load(textured_mesh_file, force='scene')
        trimesh_scene.apply_transform(self.alignment)

        return trimesh_scene

    def instance_mesh(self, vertices, triangles):
        face_colors = self.mesh_background_face_colors(triangles)

        df = self.annotations_to_dataframe(self.annotations)
        for i, row in df.iterrows():
            object_id = row['objectId']
            object_label = row['objectLabel']
            part_id = row['partId']
            part_label = row['partLabel']
            label = f'{object_label}:{part_label}'
            label_hash = self.string_to_hash_int(label)
            color = np.asarray(self.cmap(label_hash))
            
            # lighten color if the semantic category is wall, floor, ceiling
            object_semantic_id = self.object_semantic_id(object_label)
            if object_semantic_id in [1, 2, 3] or object_label.lower().startswith('remove'):
                color = lighten_color(color[:3])

            tri_indices = self.part_triangles(object_id, part_id)
            face_colors[tri_indices] = color
        
        tri_mesh = trimesh.Trimesh(vertices=vertices, faces=triangles, face_colors=face_colors, process=False)
        mesh = pyrender.Mesh.from_trimesh(tri_mesh, smooth=False)
        return pyrender.Node(mesh=mesh, matrix=self.alignment)

    @staticmethod
    def draw_box(obb, color, radius=0.01, sections=5):
        obb_centroid = np.asarray(obb['centroid'])
        vec = np.asarray(obb['normalizedAxes'])
        lengths = np.asarray(obb['axesLengths'])
        d0 = vec[0:3] * lengths[0] / 2
        d1 = vec[3:6] * lengths[1] / 2
        d2 = vec[6:9] * lengths[2] / 2
        p0 = obb_centroid - d0 + d1 + d2
        p1 = obb_centroid - d0 + d1 - d2
        p2 = obb_centroid + d0 + d1 - d2
        p3 = obb_centroid + d0 + d1 + d2

        p4 = obb_centroid - d0 - d1 + d2
        p5 = obb_centroid - d0 - d1 - d2
        p6 = obb_centroid + d0 - d1 - d2
        p7 = obb_centroid + d0 - d1 + d2
        obb_mesh = trimesh.Trimesh()
        obb_mesh += trimesh.creation.cylinder(segment=[p0, p1], radius=radius, sections=sections)
        obb_mesh += trimesh.creation.cylinder(segment=[p0, p3], radius=radius, sections=sections)
        obb_mesh += trimesh.creation.cylinder(segment=[p1, p2], radius=radius, sections=sections)
        obb_mesh += trimesh.creation.cylinder(segment=[p2, p3], radius=radius, sections=sections)

        obb_mesh += trimesh.creation.cylinder(segment=[p4, p5], radius=radius, sections=sections)
        obb_mesh += trimesh.creation.cylinder(segment=[p4, p7], radius=radius, sections=sections)
        obb_mesh += trimesh.creation.cylinder(segment=[p5, p6], radius=radius, sections=sections)
        obb_mesh += trimesh.creation.cylinder(segment=[p6, p7], radius=radius, sections=sections)

        obb_mesh += trimesh.creation.cylinder(segment=[p0, p4], radius=radius, sections=sections)
        obb_mesh += trimesh.creation.cylinder(segment=[p1, p5], radius=radius, sections=sections)
        obb_mesh += trimesh.creation.cylinder(segment=[p2, p6], radius=radius, sections=sections)
        obb_mesh += trimesh.creation.cylinder(segment=[p3, p7], radius=radius, sections=sections)
        obb_mesh.visual.vertex_colors = color
        return obb_mesh

    def draw_obb(self, obb, vertices, color, add_arrows=True, opacity=1.0):
        def modify_opacity(color, opacity):
            new_color = color.copy()
            new_color[3] = opacity
            return new_color
        
        scale = np.linalg.norm(np.amax(vertices, axis=0) - np.amin(vertices, axis=0))
        arrow_length = max(min(scale * 0.7, 0.8), 0.4)
        obb_arrows = []
        if add_arrows:
            front_arrow = self.translation_arrow(obb['centroid'], obb['front'], 
                modify_opacity(ArrowColor.ORANGE_LIGHT, opacity), modify_opacity(ArrowColor.ORANGE_DARK, opacity), arrow_length
            )
            if np.dot(obb['up'], [0, 0, 1]) > 0.9:
                obb_arrows = [front_arrow]
            else:
                up_arrow = self.translation_arrow(obb['centroid'], obb['up'],
                    modify_opacity(ArrowColor.BLUE_LIGHT, opacity), modify_opacity(ArrowColor.BLUE_DARK, opacity), arrow_length
                )
                obb_arrows = [up_arrow, front_arrow]
        
        obb_box = self.draw_box(obb, color)
        obb_mesh = trimesh.util.concatenate([obb_box] + obb_arrows)
        return obb_mesh

    def obb_mesh(self, vertices, triangles):
        face_colors = self.mesh_background_face_colors(triangles)

        df = self.annotations_to_dataframe(self.annotations)
        objects = self.annotations['objects']
        obb_meshes = []
        for i, row in df.iterrows():
            object_id = row['objectId']
            object_label = row['objectLabel']
            base_part_label = object_label + ':' + object_label.split('.')[0] + '.1'
            label_hash = self.string_to_hash_int(base_part_label)
            color = np.asarray(self.cmap(label_hash))

            # lighten color if the semantic category is wall, floor, ceiling
            object_semantic_id = self.object_semantic_id(object_label)
            if object_semantic_id in [1, 2, 3] or object_label.lower().startswith('remove'):
                color = lighten_color(color[:3])

            tri_indices = self.object_triangles(object_id)
            face_colors[tri_indices] = color

            obj = objects[object_id-1]
            if not object_label.lower().startswith('remove'):
                obb = obj['obb']
                object_vertices = vertices[np.unique(triangles[tri_indices])]
                # no arrows for ceiling and floor
                add_arrows = False if object_semantic_id in [1, 2] else True
                opacity = 0.7 if object_semantic_id in [3] else 1.0
                obb_mesh = self.draw_obb(obb, object_vertices, color, add_arrows, opacity)
                obb_meshes.append(obb_mesh)

        obj_trimesh = trimesh.Trimesh(vertices=vertices, faces=triangles, face_colors=face_colors, process=False)
        tri_mesh = trimesh.util.concatenate([obj_trimesh] + obb_meshes)
        mesh = pyrender.Mesh.from_trimesh(tri_mesh, smooth=False)
        return pyrender.Node(mesh=mesh, matrix=self.alignment)

    def articulation_mesh(self, vertices, triangles):
        face_colors = self.mesh_background_face_colors(triangles)

        df = self.annotations_to_dataframe(self.annotations)
        parts = self.annotations['parts']
        arrow_meshes = []
        for i, row in df.iterrows():
            object_id = row['objectId']
            object_label = row['objectLabel']
            part_id = row['partId']
            part_label = row['partLabel']
            part = parts[part_id-1]
            articulations = part.get('articulations')
            if articulations is None:
                continue
            articulation = articulations[0]

            label = f'{object_label}:{part_label}'
            label_hash = self.string_to_hash_int(label)
            color = np.asarray(self.cmap(label_hash))

            object_semantic_id = self.object_semantic_id(object_label)
            if object_semantic_id in [1, 2, 3] or object_label.lower().startswith('remove'):
                color = lighten_color(color[:3])

            tri_indices = self.part_triangles(object_id, part_id)
            face_colors[tri_indices] = color

            # rotation
            if articulation['type'] == 'rotation':
                part_vertices = vertices[np.unique(triangles[tri_indices])]
                scale = np.linalg.norm(np.amax(part_vertices, axis=0) - np.amin(part_vertices, axis=0))
                arrow_length = max(min(scale * 0.7, 0.8), 0.4)
                arrow = self.rotation_arrow(articulation['origin'], articulation['axis'], ArrowColor.GREEN_LIGHT, ArrowColor.GREEN_DARK, arrow_length)
            elif articulation['type'] == 'translation':
                arrow_length = articulation['rangeMax'] - articulation['rangeMin']
                assert arrow_length > 0
                arrow = self.translation_arrow(articulation['origin'], articulation['axis'], ArrowColor.RED_LIGHT, ArrowColor.RED_DARK, arrow_length)
            else:
                log.warning("Unknown motion type")
            arrow_meshes.append(arrow)
        
        obj_trimesh = trimesh.Trimesh(vertices=vertices, faces=triangles, face_colors=face_colors, process=False)
        tri_mesh = trimesh.util.concatenate([obj_trimesh] + arrow_meshes)
        mesh = pyrender.Mesh.from_trimesh(tri_mesh, smooth=False)
        return pyrender.Node(mesh=mesh, matrix=self.alignment)

    def render_turntable(self, camera_poses, name):
        frames = []
        frame_names = []
        for i, camera_pose in enumerate(camera_poses):
            self.visualizer.set_camera_pose(camera_pose)
            color, _ = self.visualizer.render()
            image = Image.fromarray(color.astype('uint8'), 'RGBA')
            frames.append(image)
            frame_names.append(name + f'.{i}')
        return frames, frame_names

    @staticmethod
    def export_frame(frame_name, frame, output_dir, image_format='.png'):
        frame.save(os.path.join(output_dir, str(frame_name) + image_format))

    def export_frames(self, frame_names, frames, output_dir, image_format='.png'):
        if len(frames) == 0:
            return
        io.ensure_dir_exists(output_dir)

        frames_dict = dict(zip(frame_names, frames))
        cpu_num = self.cfg.cpu_num
        if cpu_num > 1:
            with Pool(processes=cpu_num) as pool:
                pool.starmap(AnnotationVisualize.export_frame,
                        [(k, v, output_dir, image_format) for k, v in frames_dict.items()])
        else:
            for k, v in frames_dict.items():
                AnnotationVisualize.export_frame(k, v, output_dir, image_format)

    def initialize_camera(self):
        self.visualizer.reset_camera()
        self.visualizer.set_world_up(self.world_up)
        self.visualizer.hfov = self.hfov
        self.visualizer.scene_centroid = self.scene_centroid
        self.visualizer.scene_scale = self.scene_scale
        self.visualizer.initialize_camera()
        self.visualizer.set_camera_pose_by_angle()
    
    def export_video(self, frames, output, fps=30):
        import cv2
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video = cv2.VideoWriter(output, fourcc, fps, (self.visualizer.resolution[0],self.visualizer.resolution[1]))
        for frame in frames:
            frame = frame.convert('RGB')
            cv_frame = cv2.cvtColor(np.asarray(frame), cv2.COLOR_RGB2BGR)
            video.write(cv_frame)
        
        video.release()
        cv2.destroyAllWindows()

    def render(self, output_dir, use_cameras=None):
        io.ensure_dir_exists(os.path.join(output_dir, self.scan_id))

        vertices, vertex_colors, vertex_normals, triangles = self._construct_ply_mesh()

        textured_scene = self.textured_scene()
        self.visualizer.set_scene(textured_scene)
        
        if use_cameras is None:
            self.scene_centroid = self.visualizer.scene.centroid
            self.scene_scale = self.visualizer.scene.scale
            
            self.initialize_camera()

            turntable_step = 1
            camera_pose = self.visualizer.camera_pose
            camera_poses = []
            for i, angle_i in enumerate(range(0, 360, turntable_step)):
                angle = np.pi / 180 * angle_i + 4*np.pi/4.0
                transform = np.eye(4)
                transform[:3, :3] = R.from_rotvec(angle * self.visualizer._world_up).as_matrix()
                tmp_pose = np.dot(transform, camera_pose)
                camera_poses.append(tmp_pose)

        fps = 30
        log.info('Render textured turntable')
        frames, frame_names = self.render_turntable(camera_poses, f'{self.scan_id}.textured')
        self.visualizer.reset()
        self.initialize_camera()
        self.export_video(frames, os.path.join(output_dir, self.scan_id, f'{self.scan_id}.textured.mp4'), fps=fps)

        log.info('Render instance turntable')
        instance_mesh = self.instance_mesh(vertices, triangles)
        self.visualizer.add_node(instance_mesh)
        frames, frame_names = self.render_turntable(camera_poses, f'{self.scan_id}.instance')
        self.export_video(frames, os.path.join(output_dir, self.scan_id, f'{self.scan_id}.instance.mp4'), fps=fps)
        self.visualizer.remove_node(instance_mesh)

        log.info('Render obb turntable')
        obb_mesh = self.obb_mesh(vertices, triangles)
        self.visualizer.add_node(obb_mesh)
        frames, frame_names = self.render_turntable(camera_poses, f'{self.scan_id}.obb')
        self.export_video(frames, os.path.join(output_dir, self.scan_id, f'{self.scan_id}.obb.mp4'), fps=fps)
        self.visualizer.remove_node(obb_mesh)

        log.info('Render articulation turntable')
        articulation_mesh = self.articulation_mesh(vertices, triangles)
        self.visualizer.add_node(articulation_mesh)
        frames, frame_names = self.render_turntable(camera_poses, f'{self.scan_id}.articulation')
        self.export_video(frames, os.path.join(output_dir, self.scan_id, f'{self.scan_id}.articulation.mp4'), fps=fps)
        self.visualizer.remove_node(articulation_mesh)

        self.visualizer.reset()
        return camera_poses

@hydra.main(config_path="config", config_name="config", version_base="1.2")
def main(cfg : DictConfig):
    scan_paths = io.get_folder_list(cfg.input_dir, join_path=True)

    scans_df = []
    for scan_path in scan_paths:
        scan_id = re.findall(r"scene\_[0-9]{5}\_[0-9]{2}", scan_path)[0]
        scene_id = '_'.join(scan_id.split('_')[:-1])
        row = pd.DataFrame([[scene_id, scan_id, scan_path]], columns=['sceneId', 'scanId', 'scanPath'])
        scans_df.append(row)
    scans_df = pd.concat(scans_df)

    if cfg.scenes:
        scene_ids = cfg.scenes
    else:
        scene_ids = scans_df['sceneId'].unique()
    
    for scene_id in tqdm(scene_ids):
        scans = scans_df[scans_df['sceneId'] == scene_id]
        for i, scan in scans.iterrows():
            log.info(f'Render scan {scan.scanId}')
            # render reference scan
            if i == 0:
                annotation_viz = AnnotationVisualize(cfg, scan.scanPath)
                camera_poses = annotation_viz.render(cfg.output_dir)
            # render re-scans with same camera view points
            else:
                annotation_viz.update_scan(scan.scanPath)
                annotation_viz.render(cfg.output_dir, camera_poses)

if __name__ == "__main__":
    main()