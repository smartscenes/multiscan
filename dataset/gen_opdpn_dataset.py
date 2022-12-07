import os
import h5py
import numpy as np
import torch
from tqdm import tqdm
import shutil
import random
from dgl import backend as F
from dgl.geometry import farthest_point_sampler

import hydra
from omegaconf import DictConfig

from multiscan.utils import io

def set_random_seed(seed):
    np.random.seed(seed)
    torch.set_rng_state(torch.manual_seed(seed).get_state())
    random.seed(seed)

def fps(pos, npoints, start_idx=None):
    ctx = F.context(pos)
    B, N, C = pos.shape
    pos = pos.reshape(-1, C)
    dist = F.zeros((B * N), dtype=pos.dtype, ctx=ctx)
    if start_idx is None:
        start_idx = F.randint(shape=(B,), dtype=F.int64,
                              ctx=ctx, low=0, high=N - 1)
    else:
        if start_idx >= N or start_idx < 0:
            raise ValueError("Invalid start_idx, expected 0 <= start_idx < {}, got {}".format(
                N, start_idx))
        start_idx = F.full_1d(B, start_idx, dtype=F.int64, ctx=ctx)
    result = F.zeros((npoints * B), dtype=torch.int64, ctx=ctx)
    farthest_point_sampler(pos, B, npoints, dist, start_idx, result)
    return result.reshape(B, npoints)

@hydra.main(config_path="config", config_name="config", version_base="1.2")
def main(cfg : DictConfig):
    set_random_seed(cfg.random_seed)

    sets = ['train', 'val', 'test']
    num_points = 4096
    io.ensure_dir_exists(cfg.output_path)
    for each_set in sets:
        input_h5path = os.path.join(cfg.input_path, f'articulated_objects.{each_set}.h5')
        output_h5path = os.path.join(cfg.output_path, f'opdpn.{each_set}.h5')
        
        shutil.copy2(input_h5path, output_h5path)

        h5file = h5py.File(output_h5path, 'r+')
        for key in tqdm(h5file.keys()):
            h5instance = h5file[key]
            
            pts = h5instance['pts'][:]
            part_semantic_masks = h5instance["part_semantic_masks"][:]
            part_instance_masks = h5instance["part_instance_masks"][:]

            if pts.shape[0] == num_points:
                input_pts = pts
            else:
                xyz = pts[:, :3]
                pcd = torch.from_numpy(xyz.reshape((1, xyz.shape[0], xyz.shape[1])))
                point_idx = fps(pcd, num_points)[0].cpu().numpy()
                input_pts = pts[point_idx, :]
                part_semantic_masks = part_semantic_masks[point_idx]
                part_instance_masks = part_instance_masks[point_idx]

            assert part_semantic_masks.shape[0] == num_points
            assert part_instance_masks.shape[0] == num_points
            assert input_pts.shape[0] == num_points

            # normalize color from 0~1 to -1~1
            input_pts[:, 3:6] = input_pts[:, 3:6] / 0.5 - 1.0

            del h5instance['pts']
            del h5instance['part_semantic_masks']
            del h5instance['part_instance_masks']
            h5instance.create_dataset('pts', shape=input_pts.shape, data=input_pts.astype(np.float32),
                                        compression='gzip')
            h5instance.create_dataset('part_semantic_masks', shape=part_semantic_masks.shape,
                                        data=part_semantic_masks.astype(np.int32),
                                        compression='gzip')
            h5instance.create_dataset('part_instance_masks', shape=part_instance_masks.shape,
                                        data=part_instance_masks.astype(np.int32),
                                        compression='gzip')
        h5file.close()


if __name__ == "__main__":
    main()
