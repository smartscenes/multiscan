import os
import re
import h5py
import logging
import torch
import numpy as np
import pandas as pd
from tqdm import tqdm

import hydra
from omegaconf import DictConfig

from multiscan.utils import io

log = logging.getLogger(__name__)

class PartSegmentation:
    def __init__(self, input_hdf5):
        self.stats = pd.DataFrame()
        assert io.file_exist(input_hdf5, ext='.h5'), f'Cannot open input hdf5 file {input_hdf5}'
        self.h5file = h5py.File(f'{input_hdf5}', 'r')

    @staticmethod
    def get_scan_id(key):
        return re.findall(r"scene\_[0-9]{5}\_[0-9]{2}", key)[0]

    def convert(self, output_path):
        io.ensure_dir_exists(output_path)
        
        for key in tqdm(self.h5file.keys()):
            scan_id = self.get_scan_id(key)
            h5instance = self.h5file[key]

            num_parts = h5instance.attrs['numParts']
            object_id = h5instance.attrs['objectId']
            part_labels = h5instance.attrs['partLabels']
            has_additional_vertices = h5instance.attrs['has_additional_vertices']
            pts = h5instance['pts'][:]
            faces = h5instance['faces'][:]
            transformation_back = h5instance['transformation_back'][:]
            if has_additional_vertices:
                additional2original_vertex_match = h5instance['additional2original_vertex_match'][:]
            else:
                additional2original_vertex_match = []
            part_semantic_masks = h5instance['part_semantic_masks'][:]
            part_instance_masks = h5instance['part_instance_masks'][:]

            assert num_parts == np.unique(part_instance_masks).shape[0] - 1
            part_closed = h5instance['part_closed'][:]

            instances = np.unique(part_instance_masks)
            inst2part = {}
            for inst in instances:
                inst2part[inst] = part_labels[inst]

            part_closed_mask = np.zeros_like(part_instance_masks)
            for j in range(part_closed.shape[0]):
                if part_closed[j] == 1:
                    part_closed_mask[part_instance_masks == j+1] = 1
                else:
                    part_closed_mask[part_instance_masks == j+1] = 2

            torch.save({"key": key, "object_id": object_id, 'inst2part': inst2part,
                        "xyz": pts[:, :3], "rgb": pts[:, 3:6]*255.0, "normal": pts[:, 6:9], 'faces': faces,
                        "sem_labels": part_semantic_masks-1, "instance_ids": part_instance_masks,
                        'transformation_back': transformation_back,
                        'additional2original_vertex_match': additional2original_vertex_match, 
                        'part_closed_mask': part_closed_mask},
                        os.path.join(output_path, f'{scan_id}_{object_id}.pth'))

@hydra.main(config_path="config", config_name="config", version_base="1.2")
def main(cfg : DictConfig):
    hdf5_files = io.get_file_list(cfg.input_path, ext='.h5', join_path=True)
    for hdf5_file in hdf5_files:
        split = hdf5_file.split('.')[-2]
        log.info(f'Processing split {split}')
        ps = PartSegmentation(hdf5_file)
        ps.convert(os.path.join(cfg.output_path, split))

if __name__ == "__main__":
    main()