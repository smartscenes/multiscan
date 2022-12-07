import os
import numpy as np
import pandas as pd
import logging
import trimesh
import h5py
from tqdm import tqdm

import hydra
from omegaconf import DictConfig

from multiscan.utils import io
from core import Preprocess

log = logging.getLogger(__name__)

class ArticulatedDataset(Preprocess):
    def __init__(self, cfg, scan_dir):
        super().__init__(cfg, scan_dir)

        if self.debug:
            log.setLevel(logging.DEBUG)

        self.min_pts = 4096

    @staticmethod
    def get_pose_from_obb(front_axis, up_axis, obb_centroid):
        front = np.asarray(front_axis)
        front = front / np.linalg.norm(front)
        up = np.asarray(up_axis)
        up = up / np.linalg.norm(up)
        right = np.cross(up, front)
        orientation = np.eye(4)
        orientation[:3, :3] = np.stack([right, up, front], axis=0)
        translation = np.eye(4)
        translation[:3, 3] = -np.asarray(obb_centroid)
        return np.dot(orientation, translation)

    def process(self, output_path, h5file):
        try:
            super().process(os.path.dirname(output_path))
        except Exception as e:
            log.error(f'Error: input scan dir {self.input_path} does not match pattern scene_xxxxx_xx')
            return

        objects = self.annotations['objects']
        scan_mesh = self.construct_trimesh()
        for obj in objects:
            self.process_object(obj, scan_mesh, h5file)

    def process_object(self, obj, scan_mesh, h5file):
        obj_label = obj['label']
        if obj_label.lower().startswith('remove'):
            return
        obj_id = obj['objectId']
        obj_part_ids = obj['partIds']
        parts = self.annotations['parts']
        
        # check if object has valid articulated parts
        has_valid_articulation = False
        for part_id in obj_part_ids:
            part = parts[part_id-1]
            part_label = part['label']
            articulation = part['articulations'][0] if part.get('articulations', []) else None
            semantic_id = self.part_semantic_id(obj_label, part_label)
            if articulation and semantic_id > 1:
                has_valid_articulation = True
        
        if not has_valid_articulation:
            return

        # get object pose
        obb = obj['obb']
        object_transformation = self.get_pose_from_obb(obb['front'], obb['up'], obb['centroid'])
        mesh = scan_mesh.copy()
        mesh.apply_transform(object_transformation)

        part_meshes = []
        part_semantic_mask = []
        part_instance_mask = []
        articulation_data = {
            'motion_types': [],
            'motion_origins': [],
            'motion_axes': [],
            'motion_ranges': [],
            'motion_states': [],
            'part_closed': [],
        }
        count = 0
        id2instance_id = {}
        part_names = ['static']
        for part_id in obj_part_ids:
            part = parts[part_id-1]
            part_label = part['label']
            parent_id = part.get('parentId', 0)
            part_tri_indices = self.part_triangles(obj_id, part_id)
            part_mesh = mesh.submesh([part_tri_indices], only_watertight=False, append=True)
            part_meshes.append(part_mesh)
            
            articulation = part['articulations'][0] if part.get('articulations', []) else None
            semantic_id = self.part_semantic_id(obj_label, part_label)
            if parent_id > 0:
                parent_part = parts[parent_id-1]
                parent_label = parent_part['label']
                parent_semantic_id = self.part_semantic_id(obj_label, parent_label)
                if semantic_id > 1 and articulation:
                    count += 1
                    instance_id = count
                    id2instance_id[part_id] = instance_id

                    articulation_data['motion_types'].append(0 if articulation['type'] == 'rotation' else 1)
                    articulation_data['motion_origins'].append(articulation['origin'])
                    articulation_data['motion_axes'].append(articulation['axis'])
                    articulation_data['motion_ranges'].append([articulation['rangeMin'], articulation['rangeMax']])
                    articulation_data['motion_states'].append(articulation['state'])
                    articulation_data['part_closed'].append(articulation['isClosed'])
                    part_names.append(part_label)
                elif parent_semantic_id > 1 and id2instance_id.get(parent_id):
                    semantic_id = parent_semantic_id
                    instance_id = id2instance_id[parent_id]
                else:
                    semantic_id = 1
                    instance_id = 0
            else:
                semantic_id = 1
                instance_id = 0

            part_semantic_mask.append(np.ones(part_mesh.vertices.shape[0]) * semantic_id)
            part_instance_mask.append(np.ones(part_mesh.vertices.shape[0]) * instance_id)

        part_semantic_mask = np.concatenate(part_semantic_mask)
        part_instance_mask = np.concatenate(part_instance_mask)
        
        object_mesh = trimesh.util.concatenate(part_meshes)
        assert len(object_mesh.vertices) == len(part_semantic_mask)
        assert len(object_mesh.vertices) == len(part_instance_mask)
        object_data = {
            'vertices': object_mesh.vertices,
            'vertex_colors': object_mesh.visual.vertex_colors[:, :3],
            'vertex_normals': object_mesh.vertex_normals,
            'faces': object_mesh.faces,
        }
        if object_mesh.vertices.shape[0] < self.min_pts:
            add_vertices, add_colors, add_normals, fid = self.add_points(object_mesh, self.min_pts - object_mesh.vertices.shape[0])
            semantic_ids = part_semantic_mask[object_mesh.faces[fid]]
            instance_ids = part_instance_mask[object_mesh.faces[fid]]

            assert np.all([np.array_equal(semantic_ids[:, 0], semantic_ids[:, i]) for i in range(1, semantic_ids.shape[1])])
            assert np.all([np.array_equal(instance_ids[:, 0], instance_ids[:, i]) for i in range(1, instance_ids.shape[1])])
            
            part_semantic_mask = np.concatenate((part_semantic_mask, semantic_ids[:, 0]))
            part_instance_mask = np.concatenate((part_instance_mask, instance_ids[:, 0]))

            additional_match = self.get_closest_pt_ids(object_data['vertices'], object_data['faces'], fid, add_vertices)
            
            object_data['vertices'] = np.concatenate((object_data['vertices'], add_vertices), axis=0)
            object_data['vertex_normals'] = np.concatenate((object_data['vertex_normals'], add_normals), axis=0)
            object_data['vertex_colors'] = np.concatenate((object_data['vertex_colors'], add_colors), axis=0)
            
            object_data['additional2original_vertex_match'] = additional_match

        has_additional_vertices = True if object_data.get('additional2original_vertex_match', None) is not None else False

        pts = np.zeros((object_data['vertices'].shape[0], 9))
        pts[:, :3] = object_data['vertices']
        pts[:, 3:6] = object_data['vertex_colors'] / 255.0
        pts[:, 6:9] = object_data['vertex_normals']

        motion_types = np.asarray(articulation_data['motion_types']).astype(np.int32)
        motion_origins = np.asarray(articulation_data['motion_origins'])
        tmp_origins = np.column_stack((motion_origins, np.ones(motion_origins.shape[0])))
        tmp_origins = tmp_origins.dot(object_transformation.transpose())
        
        motion_origins = tmp_origins[:, :3].astype(np.float32)
        motion_axes = np.asarray(articulation_data['motion_axes'])
        motion_axes = motion_axes.dot(object_transformation[:3, :3].transpose()).astype(np.float32)
        motion_ranges = np.asarray(articulation_data['motion_ranges']).astype(np.float32)
        motion_states = np.asarray(articulation_data['motion_states']).astype(np.float32)
        part_closed = np.asarray(articulation_data['part_closed']).astype(bool)

        instance_name = f'{self.scan_id}_{obj_id}'
        h5instance = h5file.require_group(instance_name)
        h5instance.attrs['objectId'] = obj_id
        h5instance.attrs['numParts'] = count
        h5instance.attrs['partLabels'] = part_names
        h5instance.attrs['has_additional_vertices'] = has_additional_vertices
        h5instance.create_dataset('pts', shape=pts.shape, data=pts.astype(np.float32), compression='gzip')
        h5instance.create_dataset('faces', shape=object_data['faces'].shape, data=object_data['faces'].astype(np.float32), compression='gzip')
        h5instance.create_dataset('part_semantic_masks', shape=part_semantic_mask.shape,
                                  data=part_semantic_mask.astype(np.int32),
                                  compression='gzip')
        h5instance.create_dataset('part_instance_masks', shape=part_instance_mask.shape,
                                  data=part_instance_mask.astype(np.int32),
                                  compression='gzip')
        h5instance.create_dataset('motion_types', data=motion_types.astype(np.float32), compression='gzip')
        h5instance.create_dataset('motion_origins', shape=motion_origins.shape, data=motion_origins.astype(np.float32),
                                  compression='gzip')
        h5instance.create_dataset('motion_axes', shape=motion_axes.shape, data=motion_axes.astype(np.float32),
                                  compression='gzip')
        h5instance.create_dataset('motion_ranges', shape=motion_ranges.shape, data=motion_ranges.astype(np.float32),
                                  compression='gzip')
        h5instance.create_dataset('motion_states', shape=motion_states.shape, data=motion_states.astype(np.float32),
                                  compression='gzip')
        h5instance.create_dataset('part_closed', shape=part_closed.shape, data=part_closed.astype(bool),
                                  compression='gzip')
        transformation_back = np.linalg.inv(object_transformation).flatten(order='F').astype(np.float32)
        h5instance.create_dataset('transformation_back', shape=transformation_back.shape,
                                  data=transformation_back.astype(np.float32),
                                  compression='gzip')
        if has_additional_vertices:
            h5instance.create_dataset('additional2original_vertex_match',
                                      shape=object_data['additional2original_vertex_match'].shape,
                                      data=object_data['additional2original_vertex_match'].astype(np.int32),
                                      compression='gzip')


    def add_points(self, mesh, num_points):
        add_points_num = num_points

        samples, fid = trimesh.sample.sample_surface(mesh, add_points_num)
        bary = trimesh.triangles.points_to_barycentric(triangles=mesh.triangles[fid], points=samples)
        normals = trimesh.unitize(
            (mesh.vertex_normals[mesh.faces[fid]] * trimesh.unitize(bary).reshape((-1, 3, 1))).sum(axis=1))
        colors_all = mesh.visual.vertex_colors[:, :3]
        colors = (colors_all[mesh.faces[fid]] * bary.reshape((-1, 3, 1))).sum(axis=1)

        return samples, colors.astype(np.uint8), normals, fid

    def get_closest_pt_ids(self, vertices, faces, facets, pts):
        ids = []
        for i, pt in enumerate(pts):
            facet = faces[facets[i]]
            vertex_3 = vertices[facet, :]
            dist_3 = np.linalg.norm(vertex_3 - pt, axis=1)
            closest = facet[np.argsort(dist_3)[0]]
            ids.append(closest)
        return np.asarray(ids)


@hydra.main(config_path="config", config_name="config", version_base="1.2")
def main(cfg : DictConfig):
    scan_dirs = io.get_folder_list(cfg.input_path, join_path=True)
    scans_split = pd.read_csv(cfg.scans_split_csv)
    io.ensure_dir_exists(cfg.output_path)

    splits = ['train', 'val', 'test']
    for split in splits:
        output_path = os.path.join(cfg.output_path, f'articulated_objects.{split}.h5')
        h5file = h5py.File(output_path, 'w')
        scans = scans_split[scans_split['split'] == split]
        for i, row in tqdm(scans.iterrows(), total=scans.shape[0]):
            scan_id = row['scanId']
            scan_dir = os.path.join(cfg.input_path, scan_id)
            assert scan_dir in scan_dirs
            
            ad = ArticulatedDataset(cfg, scan_dir)
            ad.process(output_path, h5file)

if __name__ == "__main__":
    main()