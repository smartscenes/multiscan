import os
from PIL import Image
import numpy as np
import open3d as o3d
import tempfile
import zlib

from multiscan.utils import io



def align_color2depth(o3d_color, o3d_depth, fast=True):
    # use metadata to get depth map size can be faster
    color_data = np.asarray(o3d_color)
    depth_data = np.asarray(o3d_depth)
    if np.shape(color_data)[0:2] != np.shape(depth_data)[0:2]:
        color = Image.fromarray(color_data)
        depth = Image.fromarray(depth_data)
        if fast:
            color = color.resize(depth.size, Image.NEAREST)
        else:
            color = color.resize(depth.size)
        return o3d.geometry.Image(np.asarray(color))
    return o3d_color

# convert intrinsic_depth.txt in ScanNet to Open3D format
def intrinsic_txt2json(src_file, dst_file, width, height):
    if io.file_exist(src_file, '.txt'):
        with open(src_file, 'r') as f:
            mat = np.zeros(shape=(4, 4))
            for i in range(4):
                mat_str = f.readline()
                mat[i, :] = np.fromstring(mat_str, dtype=float, sep=' \t')
            intrinsic = o3d.camera.PinholeCameraIntrinsic(
                width, height,
                mat[0, 0], mat[1, 1], mat[0, 2], mat[1, 2])
        dst_ext = os.path.splitext(dst_file)[1]
        if dst_ext == '.json':
            o3d.io.write_pinhole_camera_intrinsic(dst_file, intrinsic)
        else:
            raise ValueError(
                'Save intrinsic file failed, wrong destination file format {}'.format(dst_ext))
    else:
        raise IOError(
            'Save intrinsic file failed, file {} not exist'.format(src_file))

def decompress(path):
    d = zlib.decompressobj(-zlib.MAX_WBITS)
    chuck_size = 4096 * 4
    tmp = tempfile.NamedTemporaryFile(prefix=os.path.basename(path), dir=os.path.dirname(path), delete=False)

    with open(path, 'rb') as f:
        buffer = f.read(chuck_size)
        while buffer:
            outstr = d.decompress(buffer)
            tmp.write(outstr)
            buffer = f.read(chuck_size)

        tmp.write(d.flush())
        tmp.close()

    return tmp
