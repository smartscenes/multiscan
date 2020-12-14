import argparse
from scripts.reconstruct import Reconstruct
from scripts.configure import Configure
from scripts.bridge import Bridge, File
import os


def write_intrinsic_json(depth_folder, intrinsic_file):
    """transform ScanNet intrinsic file to Open3D intrinsic file

    :return: None
    """
    import functions.utils as utils
    import os
    import numpy as np
    import open3d as o3d
    depth_files = utils.get_file_list(depth_folder)
    depth = o3d.io.read_image(depth_files[0])
    depth_data = np.asarray(depth)
    width = np.shape(depth_data)[1]
    height = np.shape(depth_data)[0]
    file_name = os.path.splitext(intrinsic_file)[0]
    utils.intrinsic_txt2json(
        file_name + '.txt',
        intrinsic_file,
        width, height)


def main():
    parser = argparse.ArgumentParser(description='Reconstruct scans!')
    parser.add_argument('-inc', '--input_color', dest='input_color', action='store', required=True, help='Input directory of color frames')
    parser.add_argument('-ind', '--input_depth', dest='input_depth', action='store', required=True, help='Input directory of depth frames')
    parser.add_argument('-ini', '--input_intrinsic', dest='input_intrinsic', action='store', required=False, help='Input json file of camera intrinsic')
    parser.add_argument('-inp', '--input_poses', dest='input_poses', action='store', required=False, help='Input directory of camera poses')
    parser.add_argument('-inm', '--input_meta', dest='input_meta', action='store', required=False, help='Input meta file')
    parser.add_argument('-inconfi', '--input_confidence', dest='input_confidence', action='store', required=False, help='Input confidence file')
    parser.add_argument('-nop', '--no_parallel', dest='parallel', default=True, action='store_false', required=False, help='Run in parallel')
    parser.add_argument('-num_cpu', '--num_cpu', dest='num_cpu', action='store', type=int, required=False, help='Maximum number of cpu processes to use')
    parser.add_argument('-l', '--level', dest='level', action='store', type=int, required=False, help='Confidence map level')
    parser.add_argument('-thresh', '--thresh', dest='thresh', action='store', type=float, required=False, help='delta filter threshold')
    parser.add_argument('-s', '--step', dest='step', action='store', type=int, required=False, help='frame skip step')

    parser.add_argument('-trunc', '--trunc', dest='trunc', action='store', type=float, required=False, help='frame skip step')
    parser.add_argument('-voxel', '--voxel', dest='voxel', action='store', type=float, required=False, help='frame skip step')

    parser.add_argument('-inmem', '--in_memory', dest='in_memory', default=False, action='store_true', required=False, help='In memory operation')
    parser.add_argument('-o', '--output', dest='output', action='store', required=True, help='Output directory of reconstruction results')

    args = parser.parse_args()
    config = Configure()
    if args.input_color:
        config.setting.io.color_path = args.input_color
    if args.input_depth:
        config.setting.io.depth_path = args.input_depth
    if args.input_intrinsic:
        config.setting.io.intrinsic_path = args.input_intrinsic
    if args.input_poses:
        config.setting.io.trajectory_path = args.input_poses
    if args.input_meta:
        config.setting.io.meta_path = args.input_meta
    if args.input_confidence:
        config.setting.io.confidence_path = args.input_confidence
    if args.parallel:
        config.setting.parameters.parallel = args.parallel
    if args.num_cpu:
        config.setting.parameters.cpu_num = int(args.num_cpu)
    if args.level != None:
        config.setting.parameters.filter.level = int(args.level)
    if args.thresh != None:
        config.setting.parameters.filter.delta_thresh = float(args.thresh)
    if args.step:
        config.setting.parameters.step = int(args.step)
    if args.trunc:
        config.setting.parameters.integration.sdf_trunc = float(args.trunc)
    if args.voxel:
        config.setting.parameters.integration.voxel_len_fine = float(args.voxel)
    if args.output:
        config.setting.io.save_folder = args.output
        # level = config.setting.parameters.filter.level
        # thresh = config.setting.parameters.filter.delta_thresh
        # trunc = config.setting.parameters.integration.sdf_trunc
        # voxel = config.setting.parameters.integration.voxel_len_fine
        # param_str = '_level_'+str(level)+'_thresh_'+str(thresh)+'_trunc_'+str(trunc)+'_voxel_'+str(voxel)
        # config.setting.io.mesh_filename = os.path.basename(os.path.normpath(args.output))+param_str+'.ply
        config.setting.io.mesh_filename = os.path.basename(os.path.normpath(args.output))+'.ply'

    try:
        if args.in_memory:
            bridge = Bridge(config)
            bridge.open_all()
            bridge.preprocess()
        
            recon = Reconstruct(config, bridge)
            recon.run()

            bridge.close_all()
        else:
            recon = Reconstruct(config)
            recon.run()
    except ValueError:
        raise
    except IOError:
        raise


if __name__ == '__main__':
    main()
