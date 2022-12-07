import os
import torch
import open3d as o3d
import numpy as np
import pandas as pd
import logging
from functools import partial
from tqdm.contrib.concurrent import process_map

import hydra
from omegaconf import DictConfig

from multiscan.utils import io
from core import Preprocess

log = logging.getLogger(__name__)

class InstanceSegmentation(Preprocess):
    def __init__(self, cfg, scan_dir):
        super().__init__(cfg, scan_dir)

        if self.debug:
            log.setLevel(logging.DEBUG)
    
    def clean_mesh(self):
        mesh = self.construct_o3d_mesh()
        if self.debug:
            o3d.visualization.draw_geometries([mesh])
        
        objects = self.annotations['objects']

        remove_indices = None
        tri_indices = {}
        for obj in objects:
            obj_label = obj['label']
            obj_id = obj['objectId']
            if obj_label.lower().startswith('remove'):
                remove_indices = self.object_triangles(obj_id)
            else:
                tri_indices[obj_id] = self.object_triangles(obj_id)
        
        if remove_indices is not None:
            remove_indices = np.sort(remove_indices)
            mesh.remove_triangles_by_index(remove_indices.tolist())
            mesh.remove_unreferenced_vertices()
        
            offset = 0
            for idx in remove_indices:
                for key, val in tri_indices.items():
                    val[val > (idx - offset)] -= 1
                offset += 1
        return mesh, tri_indices

    @staticmethod
    def triangle_idx_to_vertex_idx(mesh, tri_indicies):
        face_data = np.asarray(mesh.triangles)
        selected_triangles = face_data[tri_indicies]
        vertex_indices = np.unique(selected_triangles.ravel())
        return vertex_indices

    def process(self, output_path='output'):
        try:
            super().process(output_path)
        except Exception as e:
            log.error(f'Error: input scan dir {self.input_path} does not match pattern scene_xxxxx_xx')
            return

        mesh, tri_indices = self.clean_mesh()
        face_data = np.asarray(mesh.triangles)
        sem_labels = np.full(shape=(np.asarray(mesh.vertices).shape[0]), fill_value=-1, dtype=np.int32)
        instance_ids = np.full(shape=(sem_labels.shape[0]), fill_value=-1, dtype=np.int32)
        objects = self.annotations['objects']
        inst2obj_map = {}
        inst2obj_id_map = {}
        for inst_count, obj in enumerate(objects):
            obj_label = obj['label']
            if obj_label.lower().startswith('remove'):
                continue
            obj_id = obj['objectId']
            obj_tri_indices = tri_indices[obj_id]
            selected_tri_indices = face_data[obj_tri_indices]
            unique_vertex_indices = np.unique(selected_tri_indices.ravel())

            obj_semantic_id = self.object_semantic_id(obj_label)
            sem_labels[unique_vertex_indices] = obj_semantic_id - 1 if obj_semantic_id > 0 else -1

            vertex_indicies = self.triangle_idx_to_vertex_idx(mesh, obj_tri_indices)
            if obj_semantic_id in [1, 2, 3]:
                instance_ids[vertex_indicies] = -1
            else:
                instance_ids[vertex_indicies] = inst_count
                inst2obj_map[inst_count] = obj_label
                inst2obj_id_map[inst_count] = obj_id

        # output data
        xyz = np.ascontiguousarray(np.asarray(mesh.vertices))
        rgb = np.ascontiguousarray(np.asarray(mesh.vertex_colors)) * 255.0
        normal = np.ascontiguousarray(np.asarray(mesh.vertex_normals))
        faces = np.ascontiguousarray(np.asarray(mesh.triangles))

        # separate train/val/test cases
        torch.save({"xyz": xyz.astype(np.float32), "rgb": rgb.astype(np.float32), "normal": normal.astype(np.float32), 'faces': faces,
                        "sem_labels": sem_labels.astype(np.int32), "instance_ids": instance_ids.astype(np.int32), 'inst2obj': inst2obj_map, 'inst2obj_id': inst2obj_id_map},
                        os.path.join(self.output_path, f'{self.scan_id}.pth'))

def wrap_process(i, scans, cfg, output_path):
    row  = scans.iloc[i]
    scan_id = row['scanId']
    scan_dir = os.path.join(cfg.input_path, scan_id)
    
    inst_segm = InstanceSegmentation(cfg, scan_dir)
    inst_segm.process(output_path)

@hydra.main(config_path="config", config_name="config", version_base="1.2")
def main(cfg : DictConfig):
    scan_dirs = io.get_folder_list(cfg.input_path, join_path=True)
    scans_split = pd.read_csv(cfg.scans_split_csv)

    splits = ['train', 'val', 'test']
    for split in splits:
        log.info(f'Processing split {split}')
        scans = scans_split[scans_split['split'] == split]
        process_map(partial(wrap_process, scans=scans, cfg=cfg, output_path=os.path.join(cfg.output_path, split)), range(len(scans)), chunksize=1)

if __name__ == "__main__":
    main()