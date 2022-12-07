import os
import random
import numpy as np
import trimesh
import logging
import pyrender
import matplotlib
from PIL import Image

import hydra
from omegaconf import DictConfig
from pyrender.constants import (DEFAULT_SCENE_SCALE,
                                DEFAULT_Z_FAR, DEFAULT_Z_NEAR)
from pyrender.constants import RenderFlags
from multiscan.utils import io as mts_io

os.environ['PYOPENGL_PLATFORM'] = 'egl'
log = logging.getLogger(__name__)


class Visualizer:
    def __init__(self, debug=False):
        if debug:
            log.setLevel(logging.DEBUG)
        self.debug = debug
        self.interactive = False

        self._seed = self.set_seed()
        self._cmap = None

        self.geometries = []
        self._bg_color = np.asarray([1.0, 1.0, 1.0, 0.0])
        self.scene = pyrender.Scene(bg_color=self._bg_color)
        self._world_up = np.array([0, 1, 0])
        self.ambient_color = np.asarray([1.0, 1.0, 1.0])
        self.lights = []
        self.render_flags = RenderFlags.SHADOWS_DIRECTIONAL | RenderFlags.VERTEX_NORMALS | RenderFlags.RGBA
        self.point_size = 4.0

        self.resolution = np.array([1024, 1024])
        self.yfov = np.pi/4.0
        self.hfov = np.pi/4.0
        self.znear = DEFAULT_Z_NEAR
        self.zfar = DEFAULT_Z_FAR
        self.scene_scale = DEFAULT_SCENE_SCALE
        self.scene_centroid = np.array([0, 0, 0])
        self.camera_pose = np.eye(4)
        self.camera = None

        self.renderer = None

    @staticmethod
    def get_random_cmap():
        return matplotlib.colors.ListedColormap(np.random.rand(256, 3))

    @staticmethod
    def set_seed(seed=4):
        np.random.seed(seed)
        random.seed(seed)
        return seed

    def set_world_up(self, world_up):
        self._world_up = world_up

    def set_interative(self, interactive=False):
        self.interactive = interactive
    
    def add_geometry(self, geometry, transform=None):
        tmp_geometry = geometry.copy()
        if transform is not None:
            tmp_geometry.apply_transform(transform)
        self.geometries.append(tmp_geometry)

    def add_node(self, node):
        self.scene.add_node(node)

    def remove_node(self, node):
        self.scene.remove_node(node)

    def set_scene(self, scene, transform=None):
        trimesh_scene = scene.copy()
        if transform is not None:
            trimesh_scene.apply_transform(transform)
        
        self.scene = pyrender.Scene.from_trimesh_scene(trimesh_scene, bg_color=self._bg_color)
    
    def load_mesh(self, filepath):
        if mts_io.file_exist(filepath):
            self.geometries.append(trimesh.load(filepath, force='mesh'))
        else:
            log.error(f'Error: file {filepath} does not exist')

    def load_scene(self, filepath):
        if mts_io.file_exist(filepath):
            trimesh_scene = trimesh.load(filepath, force='scene')
        else:
            log.error(f'Error: file {filepath} does not exist')
        
        self.scene = pyrender.Scene.from_trimesh_scene(trimesh_scene, bg_color=self._bg_color)

    def initialize_camera(self, automatic=True):
        if automatic:
            if self.scene_scale == 0:
                self.znear = DEFAULT_Z_NEAR
            else:
                self.znear = min(self.scene_scale, DEFAULT_Z_NEAR)
            self.zfar = max(self.scene_scale * 10.0, DEFAULT_Z_FAR)
        pcam = pyrender.PerspectiveCamera(yfov=self.yfov, znear=self.znear, zfar=self.zfar)
        self.camera = pyrender.Node(camera=pcam, matrix=self.camera_pose)
        self.scene.add_node(self.camera)
    
    def set_camera_pose(self, transform):
        self.camera_pose = transform

    def set_camera_pose_by_angle(self, angle=np.pi*0.75):
        look_at_pos = self.scene_centroid
        dist = self.scene_scale / (1 * np.tan(self.hfov))

        offset_tmp = dist * np.array([-np.cos(angle), -np.sin(angle), 1.0])
        offset_tmp = np.append(offset_tmp, [1.0])
        transform_tmp = trimesh.geometry.align_vectors([0, 0, 1], self._world_up)
        offset = transform_tmp.dot(offset_tmp)
        camera_pos = look_at_pos + offset[:3]

        forward = camera_pos - look_at_pos
        forward /= np.linalg.norm(forward)
        right = np.cross(self._world_up, forward)
        up = np.cross(forward, right)
        look_at = np.vstack((right, up, forward, camera_pos))
        cp = np.eye(4)
        cp[:3, :4] = look_at.T
        self.camera_pose = cp

    def reset(self):
        self.interactive = False

        self.geometries = []
        self.scene.clear()
        self._bg_color = np.asarray([1.0, 1.0, 1.0, 0.0])
        self.ambient_color = np.asarray([1.0, 1.0, 1.0])
        self.lights = []
        self.render_flags = RenderFlags.SHADOWS_DIRECTIONAL | RenderFlags.VERTEX_NORMALS | RenderFlags.RGBA

        self.renderer.delete()
        self.renderer = None

    def reset_camera(self):
        self.resolution = np.array([1024, 1024])
        self.yfov = np.pi/4.0
        self.hfov = np.pi/4.0
        self.znear = DEFAULT_Z_NEAR
        self.zfar = DEFAULT_Z_FAR
        self.scene_scale = DEFAULT_SCENE_SCALE
        self.scene_centroid = np.array([0, 0, 0])
        self.camera_pose = np.eye(4)
        self.camera = None

    def add_directional_light(self, color=[1.0, 1.0, 1.0], intensity=2.0):
        dl = pyrender.DirectionalLight(color=color, intensity=intensity)
        self.lights.append(dl)

    def double_faces(self):
        self.render_flags |= pyrender.constants.RenderFlags.SKIP_CULL_FACES
    
    def set_renderer(self):
        self.renderer = pyrender.OffscreenRenderer(viewport_width=self.resolution[0], viewport_height=self.resolution[1], point_size=self.point_size)
    
    def render(self, window_title='Window'):
        if self.scene is None:
            log.Error('Error: scene is empty')
            return
        
        self.scene.ambient_light = self.ambient_color
        self.scene_centroid = self.scene.centroid
        self.scene_scale = self.scene.scale

        for geometry in self.geometries:
            if isinstance(geometry, trimesh.Trimesh):
                tmp_mesh = pyrender.Mesh.from_trimesh(geometry)
                self.scene.add(tmp_mesh)
            elif isinstance(geometry, trimesh.PointCloud):
                colors = geometry.colors.astype(float) / 255.0
                tmp_pcd = pyrender.Mesh.from_points(geometry.vertices, colors=colors)
                self.scene.add(tmp_pcd)

        if self.interactive:
            pyrender.Viewer(self.scene, viewport_size=self.resolution, window_title=window_title)
        else:
            for light in self.lights:
                self.scene.add(light)

            if self.renderer is None:
                self.set_renderer()
            
            if self.camera is None:
                self.initialize_camera()
                self.set_camera_pose_by_angle()
            
            self.scene.set_pose(self.camera, pose=self.camera_pose)
            color, depth = self.renderer.render(self.scene, self.render_flags)
            return color, depth


@hydra.main(config_path="configs", config_name="config", version_base="1.2")
def main(cfg : DictConfig):
    viz = Visualizer()
    if cfg.get('interative'):
        viz.set_interative(cfg.interative)
    viz.load_scene(cfg.input_dir)
    viz.set_world_up(np.array([0, 0, 1]))
    color, depth = viz.render()
    image = Image.fromarray(color.astype('uint8'), 'RGBA')
    image.show()

if __name__ == "__main__":
    main()