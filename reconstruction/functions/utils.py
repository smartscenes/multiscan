import os
import sys
import shutil
import re
from PIL import Image
import numpy as np
import open3d as o3d
import tempfile
import zlib

def sorted_alphanum(file_list):
    """sort the file list by arrange the numbers in filenames in increasing order

    :param file_list: a file list
    :return: sorted file list
    """
    if len(file_list) <= 1:
        return file_list
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(file_list, key=alphanum_key)


def file_exist(file_path, ext=''):
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return False
    elif ext in os.path.splitext(file_path)[1] or not ext:
        return True
    return False


def folder_exist(folder_path):
    if not os.path.exists(folder_path) or os.path.isfile(folder_path):
        return False
    else:
        return True


def get_file_list(path, ext=''):
    if not os.path.exists(path):
        raise OSError('Path {} not exist!'.format(path))

    file_list = []
    for filename in os.listdir(path):
        file_ext = os.path.splitext(filename)[1]
        if (ext in file_ext or not ext) and os.path.isfile(os.path.join(path, filename)):
            file_list.append(os.path.join(path, filename))
    file_list = sorted_alphanum(file_list)
    return file_list


def make_clean_folder(path_folder):
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)
    else:
        shutil.rmtree(path_folder)
        os.makedirs(path_folder)


def print_m(msg):
    msg_color = '\033[0m'
    sys.stdout.write(f'{msg_color}{msg}{msg_color}\n')


def print_w(warning):
    warn_color = '\033[93m'
    msg_color = '\033[0m'
    sys.stdout.write(f'{warn_color}Warning: {warning} {msg_color}\n')


def print_e(error):
    err_color = '\033[91m'
    msg_color = '\033[0m'
    sys.stdout.write(f'{err_color}Error: {error} {msg_color}\n')


def align_color2depth(o3d_color, o3d_depth):
    color_data = np.asarray(o3d_color)
    depth_data = np.asarray(o3d_depth)
    if np.shape(color_data)[0:2] != np.shape(depth_data)[0:2]:
        color = Image.fromarray(color_data)
        depth = Image.fromarray(depth_data)
        color = color.resize(depth.size)
        return o3d.geometry.Image(np.asarray(color))
    return o3d_color


def intrinsic_txt2json(src_file, dst_file, width, height):
    if file_exist(src_file, '.txt'):
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
            raise ValueError('Save intrinsic file failed, wrong destination file format {}'.format(dst_ext))
    else:
        raise IOError('Save intrinsic file failed, file {} not exist'.format(src_file))


def decompress(path):
    d = zlib.decompressobj(-zlib.MAX_WBITS)
    chuck_size=4096 * 4
    tmp = tempfile.NamedTemporaryFile(prefix=os.path.basename(path), dir=os.path.dirname(path), delete=False)

    with open(path, 'rb') as f:
        buffer=f.read(chuck_size)
        while buffer:
            outstr = d.decompress(buffer)
            tmp.write(outstr)
            buffer=f.read(chuck_size)

        tmp.write(d.flush())
        tmp.close()

    return tmp