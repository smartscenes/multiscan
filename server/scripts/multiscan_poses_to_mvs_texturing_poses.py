#!/usr/bin/env python3

import argparse
import glob
import json
import numpy as np
import os


"""
This script converts multiscan camera poses to the format expected by https://github.com/nmoehrle/mvs-texturing/ (see below)

Within a scene folder a .cam file has to be given for each image.
A .cam file is structured as follows:
    tx ty tz R00 R01 R02 R10 R11 R12 R20 R21 R22
    f d0 d1 paspect ppx ppy
First line: Extrinsics - translation vector and rotation matrix (the transform from world to camera)
Second line: Intrinsics - focal length, distortion coefficients, pixel aspect ratio and principal point
The focal length is the distance between camera center and image plane normalized by dividing with the larger image dimension.
For non-zero distortion coefficients the image will be undistorted prior to the texturing process. If only d0 is non-zero then the radial distortion model of VisualSFM is assumed, otherwise the Bundler distortion model is assumed.
The pixel aspect ratio is usually 1 or close to 1. If your SfM system doesn't output it, but outputs a different focal length in x and y direction, you have to encode this here.
The principal point has to be given in unit dimensions (e.g. 0.5 0.5).
"""


def parse_camera_poses_jsonl(filename, metadata):
    pose_file = open(filename, 'r')

    color_width = metadata['color_width']
    color_height = metadata['color_height']
    max_img_dim = max(color_width, color_height)

    poses = []
    intrinsics = []

    for pose_line in pose_file:
        cam_info = json.loads(pose_line)
        trans = cam_info.get('transform', None)
        assert trans != None
        # ARKit camera pose (+x along long axis of device toward home button, +y upwards, +z away from device on screen side)
        trans = np.asarray(trans)
        trans = trans.reshape(4, 4).transpose()

        # open3d camera pose (flip y and z)
        trans = np.matmul(trans, np.diag([1, -1, -1, 1]))
        trans = trans / trans[3][3]
        poses.append(trans)

        K = cam_info.get('intrinsics', metadata['intrinsic_data'])
        K = np.asarray(K).astype(np.float32)
        K = K.reshape(3, 3).transpose()
        K = K.flatten('F').tolist()
        fx = K[0]
        fy = K[4]
        cx = K[6]
        cy = K[7]

        f = fx / max_img_dim  # assumes fx~=fy and uses just fx
        ppx = cx / color_width
        ppy = cy / color_height
        paspect = fx / fy
        d0 = 0  # assume no radial distortion
        d1 = 0  # assume no distortion

        intrinsics.append([f, d0, d1, paspect, ppx, ppy])

    return poses, intrinsics


def get_metadata(meta_file):
    meta = json.load(meta_file)
    metadata = {}
    metadata['color_width'] = meta['streams'][0]['resolution'][1]
    metadata['color_height'] = meta['streams'][0]['resolution'][0]
    metadata['depth_width'] = meta['streams'][1]['resolution'][1]
    metadata['depth_height'] = meta['streams'][1]['resolution'][0]
    metadata['num_frames'] = min(
        meta['streams'][1]['number_of_frames'], meta['streams'][0]['number_of_frames'])
    metadata['intrinsic_data'] = meta['streams'][0]['intrinsics']
    metadata['depth_format'] = meta.get('depth_unit', 'm')

    return metadata


def write_cam_file(P, intrinsics, filename):
    P = np.linalg.inv(P)  # need world-to-camera transform matrix
    tx = P[0, 3]
    ty = P[1, 3]
    tz = P[2, 3]
    R00 = P[0, 0]
    R01 = P[0, 1]
    R02 = P[0, 2]
    R10 = P[1, 0]
    R11 = P[1, 1]
    R12 = P[1, 2]
    R20 = P[2, 0]
    R21 = P[2, 1]
    R22 = P[2, 2]
    with open(filename, 'w') as f:
        f.write(' '.join(map(str, [tx, ty, tz, R00, R01, R02, R10, R11, R12, R20, R21, R22])))
        f.write('\n')
        f.write(' '.join(map(str, intrinsics)))


def read_align_transform(filename):
    align = json.load(open(filename, 'r'))
    transform = np.asarray(align['transform'], order='F').astype(np.float32)
    transform = transform.reshape(4, 4).transpose()
    transform = np.linalg.inv(transform)
    return transform

def mts_poses_to_mvs_poses(indir, outdir, frame_skip, transform_poses):
    scan_id = os.path.basename(indir)
    img_filenames = glob.glob(f'{outdir}/*.png')
    img_frame_ids = sorted([frame_skip * int(os.path.splitext(os.path.basename(f))[0]) for f in img_filenames])

    poses_file = os.path.join(indir, scan_id + '.jsonl')
    metadata_file = os.path.join(indir, scan_id + '.json')
    metadata = get_metadata(open(f'{metadata_file}', 'r'))
    poses, intrinsics = parse_camera_poses_jsonl(f'{poses_file}', metadata)

    if os.path.isfile(transform_poses):
        transform = read_align_transform(transform_poses)
        print("Alignment transform:", transform)
        poses = [np.matmul(transform, p) for p in poses]

    for i in range(len(img_frame_ids)):
        frame_i = img_frame_ids[i]
        pose_i = poses[frame_i]
        if i == 0:
            print("First pose:", pose_i)
        intrinsics_i = intrinsics[frame_i]
        # TODO: change frame id to the actual indices
        cam_filename = os.path.join(outdir, f'{i}.cam')
        write_cam_file(pose_i, intrinsics_i, cam_filename)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert multiscan pose jsonl file into camera config file used by STK')
    parser.add_argument('-i', '--indir', required=True, help='Input scan directory')
    parser.add_argument('-o', '--outdir', required=True, help='Output color image file directory')
    parser.add_argument('-f', '--frame_skip', type=int, required=True, help='Frame skip used in color/depth frame extraction')
    # parser.add_argument('-t', '--transform_poses',  action='store_true', help='Whether to transform poses by mesh alignment transform')
    parser.add_argument('-t', '--transform_poses', required=False , help='Mesh alignment transform file path')
    args = parser.parse_args()

    mts_poses_to_mvs_poses(args.indir, args.outdir, args.frame_skip, args.transform_poses)
    
