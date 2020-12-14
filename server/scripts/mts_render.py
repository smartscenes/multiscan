import os
import mitsuba
import numpy as np
import argparse
import utils

mitsuba.set_variant('scalar_spectral')

from mitsuba.core import xml, Thread, ScalarTransform4f, Transform4f, Bitmap, Struct
from mitsuba.python.xml import WriteXML
from enoki.scalar import *
import open3d as o3d
from plyfile import PlyData, PlyElement
from render import gravity_aligned_mobb

def cvt_rgba2float(filename, tmp_out_file):
    plydata = PlyData.read(filename)

    x = np.asarray(plydata['vertex']['x'])
    y = np.asarray(plydata['vertex']['y'])
    z = np.asarray(plydata['vertex']['z'])
    red = plydata['vertex']['red'].astype('float32') / 255.
    green = plydata['vertex']['green'].astype('float32') / 255.
    blue = plydata['vertex']['blue'].astype('float32') / 255.
    vertices = np.vstack((x, y, z, red, green, blue)).transpose()
    ply_vertices = [tuple(x) for x in vertices.tolist()]
    ply_vertices = np.array(ply_vertices, dtype=[('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
                                    ('red', 'f4'), ('green', 'f4'), ('blue', 'f4')])
    el = PlyElement.describe(ply_vertices, 'vertex')
    plydata.elements = [el, plydata['face']]
    plydata.write(os.path.join(os.path.dirname(filename), tmp_out_file))

    return vertices

def mts_render(filename, vertices, output):
    data = {"type": "scene", "./": {"type": "path"}}
    shape_dict = {
        "type": "ply", 'filename': filename,
        "mybsdf": {
            "type": "diffuse",
            "reflectance": {
                "type": "mesh_attribute",
                "name": "vertex_color"
                # "type": "rgb",
                # "value": [231. / 255, 181. / 255, 75. / 255],
            }
        }
    }
    emitter_dict = {"type": "constant"}
    sensor_dict = {
        "type": "perspective",
        'fov': 60,
        "myfilm": {
            "type": "hdrfilm",
            "rfilter": {"type": "gaussian"},
            "width": 1920,
            "height": 1440,
            "pixel_format": "rgba"
        },
        "mysampler": {
            "type": "independent",
            "sample_count": 64,
        }
    }

    obb_center, obb_size, trans_inv = gravity_aligned_mobb(vertices[:, 0:3], np.array((0.0,1.0,0.0)))

    rot = trans_inv
    inv_rot = np.linalg.inv(rot)
    cam_target = obb_center
    cam_translate = Transform4f.translate(cam_target)
    cam_un_translate = Transform4f.translate(-cam_target)
    world_up = Vector3f(0, 0, -1)
    cam_offvec = Vector3f(0, 0, 0)

    margin = 1.0
    radius = np.linalg.norm(obb_size) / 2.0 + margin
    cam_offset = cam_offvec + world_up
    cam_offset = rot.dot(cam_offset)
    cam_offset = 2 * radius * cam_offset / np.linalg.norm(cam_offset)
    cam_origin = cam_target + cam_offset
    cam_up = rot.dot(Vector3f(0, 1, 0))

    sensor_dict['to_world'] = ScalarTransform4f.look_at(origin=cam_origin, target=cam_target, up=cam_up)

    data['myshape'] = shape_dict
    data['mysensor'] = sensor_dict
    data['myemitter'] = emitter_dict

    scene = xml.load_dict(data)
    sensor = scene.sensors()[0]
    scene.integrator().render(scene, sensor)
    film = sensor.film()
    film.set_destination_file(os.path.splitext(output)[0]+'.exr')
    film.develop()

    img = film.bitmap(raw=True).convert(Bitmap.PixelFormat.RGB, Struct.Type.UInt8, srgb_gamma=True)
    img.write(output)

    # out = WriteXML('./test.xml')
    # out.write_dict(data)

def configure(args):
    if not utils.file_exist(args.input, '.ply'):
        utils.print_e(f'Input file {args.input} not exists')
        return False

    dir_path = os.path.dirname(args.output)
    if not utils.folder_exist(dir_path):
        utils.print_e(f'Cannot create file in folder {dir_path}')
        return False

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mitsuba2 Rendering!')
    parser.add_argument('-i', '--input', dest='input', type=str, action='store', required=True,
                        help='Input mesh ply file')
    parser.add_argument('-i', '--input', dest='input', type=str, action='store', required=True,
                        help='Input mesh ply file')
    parser.add_argument('-o', '--output', dest='output', type=str, action='store', required=True,
                        help='Output rendered png file')

    args = parser.parse_args()

    if not configure(args):
        exit(0)

    filename = os.path.realpath(args.input)
    tmp_out_file = os.path.splitext(filename)[0]+'_temp_rgba_float.ply'
    vertices = cvt_rgba2float(filename, tmp_out_file)
    mts_render(tmp_out_file, vertices, args.output)
