import os
import re
import random
import open3d as o3d
import numpy as np
import pandas as pd
import trimesh
from multiscan.utils import io
from plyfile import PlyData

class Preprocess:
    def __init__(self, cfg, scan_dir):
        self.input_path = scan_dir
        self.debug = cfg.debug
        self.cfg = cfg
        self.output_path = None
        self.plydata = None
        self.semseg_df = None
        self.annotations = None
        self.object_semantic_id_map = None
        self.scans_split = None

        self.seed = self.set_seed(cfg.random_seed)

    @staticmethod
    def set_seed(seed=1):
        np.random.seed(seed)
        random.seed(seed)
        return seed

    @property
    def scan_id(self):
        return os.path.basename(self.input_path)

    def _get_annotations(self):
        return io.read_json(os.path.join(self.input_path, f'{self.scan_id}.annotations.json'))

    def _get_plydata(self):
        return PlyData.read(os.path.join(self.input_path, f'{self.scan_id}.ply'))

    def _construct_mesh(self):
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

    def construct_o3d_mesh(self):
        vertices, vertex_colors, vertex_normals, triangles = self._construct_mesh()
        
        mesh = o3d.geometry.TriangleMesh(
                o3d.utility.Vector3dVector(vertices),
                o3d.utility.Vector3iVector(triangles)
            )
        mesh.vertex_normals = o3d.utility.Vector3dVector(vertex_normals)
        mesh.vertex_colors = o3d.utility.Vector3dVector(vertex_colors)
        return mesh

    def construct_trimesh(self):
        vertices, vertex_colors, vertex_normals, triangles = self._construct_mesh()
        return trimesh.Trimesh(vertices=vertices, faces=triangles, vertex_normals=vertex_normals, vertex_colors=vertex_colors, process=False)

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

    def _get_object_semantic_id_map(self):
        return pd.read_csv(self.cfg.object_semantic_label_map_csv)

    def _get_part_semantic_id_map(self):
        return pd.read_csv(self.cfg.part_semantic_label_map_csv)

    def _get_scans_split(self):
        return pd.read_csv(self.cfg.scans_split_csv)

    def object_semantic_id(self, object_label):
        df = self.object_semantic_id_map
        object_name = object_label.split('.')[0]
        semantic_id = df[df['objectName'] == object_name]['objectSemanticId']
        if len(semantic_id) > 0:
            return semantic_id.iat[0]
        else:
            return 0

    def part_semantic_id(self, object_label, part_label):
        object_df = self.object_semantic_id_map
        part_df = self.part_semantic_id_map
        object_name = object_label.split('.')[0]
        part_name = part_label.split('.')[0]
        object_semantic_id = object_df[object_df['objectName'] == object_name]['objectSemanticId']
        part_semantic_id = part_df[part_df['partName'] == part_name]['partSemanticId']
        if len(object_semantic_id) > 0 and len(part_semantic_id) > 0:
            return part_semantic_id.iat[0]
        else:
            # 1 as static part
            return 1

    def process(self, output_path):
        assert re.search(r"scene\_[0-9]{5}\_[0-9]{2}", self.input_path)

        self.output_path = output_path
        io.ensure_dir_exists(self.output_path)

        self.plydata = self._get_plydata()
        self.semseg_df = self.semseg_triangles()
        self.annotations = self._get_annotations()
        self.object_semantic_id_map = self._get_object_semantic_id_map()
        self.part_semantic_id_map = self._get_part_semantic_id_map()
        self.scans_split = self._get_scans_split()