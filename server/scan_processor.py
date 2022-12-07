#!/usr/bin/env python
#
# Process scans from ipad and runs recons pipeline
# Run with ./scan_processor.py (or python scan_processor.py on Windows)

import json
import logging
import os
import re
import shutil
import traceback
import requests
from glob import glob
from PIL import Image

import hydra
from hydra.utils import get_original_cwd
from omegaconf import DictConfig, OmegaConf

from multiscan.utils import io
from multiscan.meshproc import TriMesh
import util
from util import ProcessStage, TexturingMethod

FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
formatter = logging.Formatter(FORMAT)
logging.basicConfig(format=FORMAT)
log = logging.getLogger('scan_processor')
log.setLevel(logging.INFO)


# decode .mp4 video to .png images with ffmpeg
def decode_color(cfg):
    try:
        ret = 0
        if os.path.isfile(cfg.process.color_stream):
            io.make_clean_folder(cfg.process.color_dir)
            downscale= cfg.process.decode.color_downscale
            ret = io.call(['ffmpeg', '-i', cfg.process.color_stream, '-vf', 
                           f'select=not(mod(n\\,{cfg.process.decode.step})), scale=iw/{downscale}:ih/{downscale}',
                           '-vsync', 'vfr', '-start_number', '0',
                           os.path.join(cfg.process.color_dir, '%d.png')], log, desc='decode color stream', cpu_num=cfg.process.decode.cpus)

        log.info(f'Decoding color stream is ended, return code {ret}')
        return ret
    except Exception as e:
        log.error(traceback.format_exc())
        raise e


# decompress .zlib depth and confidence streams and export to images
def decode_depth(cfg):
    ret = 0
    try:
        depth_stream = cfg.process.depth_stream
        depth_out = cfg.process.depth_dir
        confidence_stream = cfg.process.confidence_stream
        metadata = io.read_json(cfg.process.meta_file)
        width = metadata.get('streams')[1]['resolution'][1]
        height = metadata.get('streams')[1]['resolution'][0]
        depth_unit = metadata.get('depth_unit', 'm')
        if io.is_non_zero_file(depth_stream):
            io.make_clean_folder(depth_out)

            env = os.environ.copy()
            env['PYTHONPATH'] = ":".join(cfg.process.scripts_path)
            ret = io.call(['python', 'depth_decode.py',
                        '-in', depth_stream, 
                        '-in_confi', confidence_stream,
                        '-o', depth_out,
                        '-W', str(width),
                        '-H', str(height),
                        '-S', str(cfg.process.decode.depth_step),
                        '-TH', str(cfg.process.decode.depth_delta),
                        '--filter',
                        '-L', str(cfg.process.decode.level),
                        '--pixel_size', str(cfg.process.decode.pixel_size),
                        '--unit', depth_unit,
                        '--format', cfg.process.decode.depth_format,
                        ], log, cfg.process.scripts_path, env=env, cpu_num=cfg.process.decode.cpus)
                
        log.info(f'Decoding depth stream is ended, return code {ret}')
        return ret
    except Exception as e:
        log.error(traceback.format_exc())
        raise e

def decode(cfg):
    ret = 0
    try:
        ret = decode_color(cfg)
        if ret != 0:
            log.error('Scan at %s aborted: decode color stream failed' % cfg.process.scan_dir)
            return ret
        ret = decode_depth(cfg)
        if ret != 0:
            log.error('Scan at %s aborted: decode depth stream failed' % cfg.process.scan_dir)
            return ret

        color_frames = io.get_file_list(cfg.process.color_dir, '.png')
        depth_frames = io.get_file_list(cfg.process.depth_dir, cfg.process.decode.depth_format)
        if len(color_frames) == 0:
            log.error('Scan at %s aborted: no decoded color images (convert failed)' % cfg.process.scan_dir)
            return ret
        if len(depth_frames) == 0:
            log.error('Scan at %s aborted: no decoded depth images (convert failed)' % cfg.process.scan_dir)
            return ret
        return ret
    except Exception as e:
        log.error(traceback.format_exc())
        raise e


def mesh_segmentation(cfg, mesh_file):
    ret = 0
    try:
        if io.is_non_zero_file(mesh_file):
            output_dir = os.path.join(os.path.dirname(mesh_file), cfg.process.segmentation.result_folder)
            io.ensure_dir_exists(output_dir)
            basename = os.path.basename(mesh_file)
            log.info(f'Start mesh segmentation with segmentator')
            kthresh_list = OmegaConf.to_object(cfg.process.segmentation.kthesh)
            for i, kthresh in enumerate(kthresh_list):
                segs_file = os.path.join(output_dir, os.path.splitext(basename)[0] + (cfg.process.segmentation.segs_ext % kthresh))
                face_based = '--face_based' if cfg.process.segmentation.face_based else ''
                ret = io.call(['./segmentator', 
                                '--input', mesh_file,
                                face_based,
                                '--kThresh', str(kthresh),
                                '--segMinVerts', str(cfg.process.segmentation.seg_min_verts),
                                '--colorWeight', str(cfg.process.segmentation.color_weight),
                                '--colorKThresh', str(cfg.process.segmentation.color_kthesh[i]),
                                '--colorSegMinVerts', str(cfg.process.segmentation.color_seg_min_verts),
                                '--scanID', cfg.process.scan_name,
                                '--output', segs_file,
                                ], log, cfg.process.segmentation.bin_path)
                # create visualize result of the segmentation
                if io.is_non_zero_file(segs_file) and cfg.process.segmentation.render:
                    log.info(f'Start creating visualization image of the segmentation')
                    
                    env = os.environ.copy()
                    env['PYTHONPATH'] = ":".join(cfg.process.scripts_path)
                    ret = io.call(['python', 'segm_viz.py', 
                                '-i', mesh_file,
                                '-segs', segs_file,
                                '-o', os.path.dirname(segs_file),
                                '--output_mesh',
                                '--width', str(cfg.process.segmentation.render_res[0]),
                                '--height', str(cfg.process.segmentation.render_res[1]),
                                ], log, cfg.process.scripts_path, env=env)
        log.info(f'Mesh segmentation is ended, return code {ret}')
        return ret
    except Exception as e:
        log.error(traceback.format_exc())
        raise e


def atlas_downscale(cfg, mesh_filename, atlas_filename):
    if cfg.process.texturing.atlas_max_size <= 0:
        return
    
    downscale_mesh_dir = cfg.process.textured_mesh_dir + f'_{cfg.process.texturing.atlas_max_size}'
    io.make_clean_folder(downscale_mesh_dir)
    mesh_atlas = glob(os.path.join(cfg.process.textured_mesh_dir, atlas_filename))
    mesh_name = os.path.splitext(mesh_filename)[0]
    obj_filename = mesh_name + '.obj'
    mtl_filename = mesh_name + '.mtl'
    shutil.copyfile(os.path.join(cfg.process.textured_mesh_dir, obj_filename), os.path.join(downscale_mesh_dir, obj_filename))
    shutil.copyfile(os.path.join(cfg.process.textured_mesh_dir, mtl_filename), os.path.join(downscale_mesh_dir, mtl_filename))
    for each_atlas in mesh_atlas:
        with Image.open(each_atlas) as im:
            width, height = im.size
            output_path = os.path.join(downscale_mesh_dir, os.path.basename(each_atlas))
            if width <= cfg.process.texturing.atlas_max_size or height <= cfg.process.texturing.atlas_max_size:
                shutil.copyfile(each_atlas, output_path)
            else:
                im1 = im.resize((cfg.process.texturing.atlas_max_size, cfg.process.texturing.atlas_max_size))
                im1.save(output_path)


def mvs_texturing(cfg):
    ret = 0
    try:
        # convert multiscan poses to mvs texturing poses
        if os.path.isdir(cfg.process.color_dir):
            mesh_align_filename = cfg.process.mesh_alignment_filename
            mesh_align_path = os.path.join(cfg.process.output_dir, mesh_align_filename)

            env = os.environ.copy()
            env['PYTHONPATH'] = ":".join(cfg.process.scripts_path)
            ret = io.call(['python', 'multiscan_poses_to_mvs_texturing_poses.py', 
                        '-i', cfg.process.scan_dir,
                        '-o', cfg.process.color_dir,
                        '-f', str(cfg.process.texturing.step),
                        '-t', mesh_align_path,
                        ], log, cfg.process.scripts_path, env=env)

            io.make_clean_folder(cfg.process.textured_mesh_dir)
            decimated_mesh_path = os.path.join(cfg.process.output_dir, cfg.process.decimated_mesh_filename)
            keep_unseen_faces = '--keep_unseen_faces' if cfg.process.texturing.keep_unseen_faces else ''
            output_mesh_basename = os.path.join(cfg.process.textured_mesh_dir, cfg.process.texturing.mesh_name % cfg.process.scan_name)
            ret = io.call(['./texrecon', '-d', cfg.process.texturing.data_term, 
                           '-o', cfg.process.texturing.outlier_removal, 
                           f'--max_texture_size={cfg.process.texturing.max_texture_size}',
                           f'--prefer_texture_size={cfg.process.texturing.prefer_texture_size}',
                           f'--min_texture_size={cfg.process.texturing.min_texture_size}',
                           f'--padding={cfg.process.texturing.padding}',
                           f'--waste_ratio={cfg.process.texturing.waste_ratio}',
                           keep_unseen_faces, cfg.process.color_dir, decimated_mesh_path, 
                           output_mesh_basename],
                           log, cfg.process.texturing.msv_bin_path, cpu_num=cfg.process.texturing.cpus)

            TriMesh.transfer_color_texture_to_vertex(output_mesh_basename+'.obj', os.path.splitext(decimated_mesh_path)[0]+'_colored.ply')
        return ret
    except Exception as e:
        log.error(traceback.format_exc())
        raise e


def get_web_scans_list(scans_list_url):
    res = requests.get(scans_list_url)
    scans_list = res.json().get('data', None)
    return scans_list


def pairwise_align(cfg):
    ret = 0
    try:
        # listing endpoint
        scans_list = get_web_scans_list(cfg.process.align.scans_list_url)
        scene_id = None
        for i, scan_dict in enumerate(scans_list):
            scan_group = scan_dict.get('group', '')
            if scan_group == 'staging' or scan_group == 'checked':
                if scan_dict.get('id') == cfg.process.scan_name:
                    scene_id = scan_dict.get('sceneName', None)

        if scene_id:
            scan_pairs = []
            scan_ids = []
            target_scan = None
            for i, scan_dict in enumerate(scans_list):
                scan_group = scan_dict.get('group', '')
                if scan_group == 'staging' or scan_group == 'checked':
                    if scan_dict.get('sceneName', None) == scene_id:
                        scan_pairs.append(scan_dict)
                        scan_ids.append(scan_dict.get('id'))
                        if 'ref' in scan_dict.get('tags', []):
                            target_scan = scan_dict
            if target_scan is None:
                ref_idx = io.sorted_alphanum(scan_ids)[1][0]
                target_scan = scan_pairs[ref_idx]
            
            if target_scan.get('id') != cfg.process.scan_name:
                staging_path = os.path.abspath(cfg.process.staging_dir)
                target_mesh_filename = cfg.reconstruction.output.decimated_mesh_filename % target_scan.get('id')
                target_mesh_filename = os.path.splitext(target_mesh_filename)[0] + '_colored.ply'
                target_mesh_path = os.path.join(
                    staging_path, target_scan.get('id'), cfg.process.output_folder, target_mesh_filename)
                source_mesh_filename = os.path.splitext(cfg.process.decimated_mesh_filename)[0] + '_colored.ply'
                source_mesh_path = os.path.join(cfg.process.output_dir, source_mesh_filename)

                env = os.environ.copy()
                env['PYTHONPATH'] = ":".join(cfg.process.scripts_path)

                tmp_dir = os.path.join(cfg.process.output_dir, cfg.process.align.tmp_folder)
                io.ensure_dir_exists(tmp_dir)
                corres_args = []
                corres_file = os.path.join(cfg.process.output_dir, cfg.process.align.tmp_folder, \
                    cfg.process.scan_name + '_to_' + target_scan.get('id') + '_align_corres.json')
                if io.is_non_zero_file(corres_file):
                    corres_args = ['--corres', corres_file]
                    
                ret = io.call(['python', 'align_pairs.py',
                            '--source_id', cfg.process.scan_name,
                            '--target_id', target_scan.get('id'),
                            '--source_mesh', source_mesh_path,
                            '--target_mesh', target_mesh_path,
                            '-o', os.path.join(cfg.process.output_dir, cfg.process.align.tmp_folder, 
                                               cfg.process.scan_name + '_to_' + target_scan.get('id') + '_align.json'),
                            ] + corres_args, log, cfg.process.scripts_path, env=env)

                if os.path.isdir(tmp_dir):
                    tmp_files = io.get_file_list(tmp_dir, '.json')
                    align_tmp_files = [file for file in tmp_files if '_align.json' in file]

                    alignments = {}
                    alignments['version'] = 'pairalign@0.0.1'
                    alignments['target_ids'] = []
                    alignments['alignments'] = []
                    for file in align_tmp_files:
                        data = io.read_json(file)
                        alignments['target_ids'].append(data['target_id'])
                        alignment = {}
                        alignment['target_id'] = data['target_id']
                        alignment['s2t_transformation'] = data['s2t_transformation']
                        alignment['error_matrix'] = data['error_matrix']
                        alignments['alignments'].append(alignment)

                    io.write_json(alignments, os.path.join(cfg.process.output_dir, cfg.process.scan_name + cfg.process.align.align_ext))
                    shutil.copyfile(os.path.join(cfg.process.output_dir, cfg.process.align.tmp_folder, cfg.process.scan_name + '_prealign.png'), 
                                    os.path.join(cfg.process.output_dir, cfg.process.scan_name + '_prealign.png'))
                    shutil.copyfile(os.path.join(cfg.process.output_dir, cfg.process.align.tmp_folder, cfg.process.scan_name + '_postalign.png'), 
                                    os.path.join(cfg.process.output_dir, cfg.process.scan_name + '_postalign.png'))
        return ret
    except Exception as e:
        log.error(traceback.format_exc())
        raise e

def update_config(proc_dict, process_list):
    if proc_dict.get('all'):
        for name in process_list:
            proc_dict[name] = True
    else:
        if proc_dict.get('from'):
            fromSeen = False
            for name in process_list:
                fromSeen = fromSeen or name == proc_dict['from']
                proc_dict[name] = fromSeen
        if proc_dict.get('actions'):
            log.info(proc_dict['actions'])
            actions = json.loads(proc_dict['actions'])
            for action in actions:
                if action in process_list:
                    proc_dict[action] = True

    return proc_dict


def process_scan_dir(path, name, config, proc=ProcessStage.PRELIMINARY):
    # Check if valid scan dir
    import index
    validNovh = index.has_scan(path)
    if not validNovh:
        msg = 'path %s not a valid scan dir' % path
        log.info(msg)
        return msg

    # Wrapper around process_scan_dir_basic but with logging to file
    fh = logging.FileHandler(os.path.join(path, 'process.log'))
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    log.addHandler(fh)
    msg = ''
    try:
        msg = process_scan_dir_basic(path, name, config, proc)
        log.info(msg)
    finally:
        log.removeHandler(fh)
        fh.close()
    return msg


def process_preliminary(config, validate):
    ret = 0
    try:
        # create thumbnails from uploaded video
        if config.get('thumbnail') and (config.get('overwrite') or validate.get('thumbnail') != 'true'):
            ret |= io.call([config.process.thumbnail.mp42thumbnail_bin,
                        config.process.output_dir, str(config.process.thumbnail.thumbnail_width)],
                        log, desc='mp4-to-thumbnail')
            ret |= io.call([config.process.thumbnail.mp42preview_bin,
                            config.process.output_dir, str(config.process.thumbnail.preview_width)],
                            log, desc='mp4-to-preview')
        else:
            log.info('skipping thumbnails')

        # Decode video to frames
        if config.get('convert') and (config.get('overwrite') or validate.get('convert') != 'true'):
            ret |= decode(config)
        else:
            log.info('skipping convert')
        
        # Open3D Reconstruction
        if config.get('recons') and (config.get('overwrite') or validate.get('recons') != 'true'):
            log.info(f'Start processing using open3d integration')

            env = os.environ.copy()
            env['PYTHONPATH'] = ":".join(config.process.reconstruction_path)
            ret = io.call(['python', 'main.py',
                        '--config-path', os.path.join(config.dump_cfg_path, '.hydra'),
                        f'reconstruction.input.color_stream={config.process.color_dir}',
                        f'reconstruction.input.depth_stream={config.process.depth_dir}',
                        f'reconstruction.input.metadata_file={config.process.meta_file}',
                        f'reconstruction.input.trajectory_file={config.process.camera_file}',
                        f'reconstruction.output.save_folder={config.process.output_dir}',
                        f'reconstruction.output.mesh_filename={config.process.mesh_filename}',
                        f'reconstruction.output.decimated_mesh_filename={config.process.decimated_mesh_filename}',
                        f'reconstruction.output.mesh_alignment_filename={config.process.mesh_alignment_filename}',
                        ], log, config.process.reconstruction_path, env=env, cpu_num=config.reconstruction.settings.cpu_num)
        else:
            log.info('skipping reconstruction')

        # render decimated mesh
        if config.get('render') and (config.get('overwrite') or validate.get('render') != 'true'):
            thumb_ext = config.process.render.low_res_ply
            thumb2_ext = config.process.render.high_res_ply
            mesh_file = os.path.join(config.process.output_dir, config.process.decimated_mesh_filename)
            thumb_path = os.path.join(config.process.output_dir, config.process.scan_name + thumb_ext)
            # higher resolution
            thumb2_path = os.path.join(config.process.output_dir, config.process.scan_name + thumb2_ext)
            if io.is_non_zero_file(mesh_file):
                log.info(f'Start creating rendered mesh thumbnail image')
                env = os.environ.copy()
                env['PYTHONPATH'] = ":".join(config.process.scripts_path)
                ret = io.call(['python', 'render.py',
                            '-i', mesh_file,
                            '-o', thumb_path,
                            '--width', str(config.process.render.low_res[0]),
                            '--height', str(config.process.render.low_res[1]),
                            '--paint_uniform_color',
                            ], log, config.process.scripts_path, env=env)

                ret = io.call(['python', 'render.py',
                            '-i', mesh_file,
                            '-o', thumb2_path,
                            '--width', str(config.process.render.high_res[0]),
                            '--height', str(config.process.render.high_res[1]),
                            '--paint_uniform_color',
                            ], log, config.process.scripts_path, env=env)
        else:
            log.info('skipping render textured mesh')

    except Exception as e:
        ret = 1
        log.error(e)

    return ret


def process_extra(config, validate):
    ret = 0
    try:
        # Texturing reconstructed mesh
        if config.get('texturing') and (config.get('overwrite') or validate.get('texturing') != 'true'):
            ret |= mvs_texturing(config)
            mesh_name = config.process.texturing.mesh_name % config.process.scan_name
            atlas_downscale(config, mesh_name + '.obj', mesh_name + '_material*.png')
        else:
            log.info('skipping texturing')

        if config.get('atlasresize'):
            mesh_name = config.process.texturing.mesh_name % config.process.scan_name
            atlas_downscale(config, mesh_name + '.obj', mesh_name + '_material*.png')
        else:
            log.info('skipping texturing')

        # textured mesh segmentation
        if config.get('segmentation') and (config.get('overwrite') or validate.get('segmentation') != 'true'):
            decimated_mesh_path = os.path.join(config.process.output_dir, config.process.decimated_mesh_filename)
            textured_mesh_file = os.path.splitext(decimated_mesh_path)[0]+'_colored.ply'
            ret |= mesh_segmentation(config, textured_mesh_file)
        else:
            log.info('skipping textured mesh segmentation')
        
        # render textured mesh
        if config.get('render') and (config.get('overwrite') or validate.get('render') != 'true'):
            thumb_ext = config.process.render.low_res_obj
            thumb2_ext = config.process.render.high_res_obj
            obj_mesh_filename = config.process.texturing.mesh_name % config.process.scan_name + '.obj'
            mesh_file = os.path.join(config.process.textured_mesh_dir, obj_mesh_filename)
            thumb_path = os.path.join(config.process.output_dir, config.process.scan_name + thumb_ext)
            # higher resolution
            thumb2_path = os.path.join(config.process.output_dir, config.process.scan_name + thumb2_ext)
            if io.is_non_zero_file(mesh_file):
                log.info(f'Start creating rendered mesh thumbnail image')
                env = os.environ.copy()
                env['PYTHONPATH'] = ":".join(config.process.scripts_path)
                ret = io.call(['python', 'render.py',
                            '-i', mesh_file,
                            '-o', thumb_path,
                            '--width', str(config.process.render.low_res[0]),
                            '--height', str(config.process.render.low_res[1]),
                            ], log, config.process.scripts_path, env=env)

                ret = io.call(['python', 'render.py',
                            '-i', mesh_file,
                            '-o', thumb2_path,
                            '--width', str(config.process.render.high_res[0]),
                            '--height', str(config.process.render.high_res[1]),
                            ], log, config.process.scripts_path, env=env)
        else:
            log.info('skipping render textured mesh')

        # align scans from same scene
        if config.get('alignpairs') and (config.get('overwrite') or validate.get('alignpairs') != 'true'):
            ret |= pairwise_align(config)
        else:
            log.info('skipping align pairs')

        # clean temporary files and dirs
        if config.get('clean'):
            if os.path.exists(config.process.color_dir):
                shutil.rmtree(config.process.color_dir)
            if os.path.exists(config.process.depth_dir):
                shutil.rmtree(config.process.depth_dir)

            # remove tmp uncompressed files
            all_files = glob(config.process.output_dir + '/*')
            file_pattern = re.compile(r'.*{}\.(depth|confidence)\.zlib.+'.format(config.process.scan_name))
            matched_files = [fi for fi in all_files if file_pattern.match(fi)]
            for tmp_file in matched_files:
                # double check
                if os.path.basename(tmp_file) != os.path.basename(config.process.confidence_stream) \
                        and os.path.basename(tmp_file) != os.path.basename(config.process.confidence_stream):
                    os.remove(tmp_file)
        else:
            log.info('skipping clean')
    except Exception as e:
        ret = 1
        log.error(e)

    return ret

def validate_process(cfg):
    validate = {}
    all_valid = True
    # check convert
    if os.path.isdir(cfg.process.color_dir) and os.path.isdir(cfg.process.depth_dir):
        validate['convert'] = 'true'
    else:
        validate['convert'] = 'false'
        all_valid = False

    # check recons
    if io.is_non_zero_file(os.path.join(cfg.process.output_dir, cfg.process.mesh_filename)) and \
        io.is_non_zero_file(os.path.join(cfg.process.output_dir, cfg.process.decimated_mesh_filename)) and \
            io.is_non_zero_file(os.path.join(cfg.process.output_dir, cfg.process.mesh_alignment_filename)):
        validate['recons'] = 'true'
    else:
        validate['recons'] = 'false'
        all_valid = False

    # check texturing
    if io.is_non_zero_file(os.path.join(cfg.process.textured_mesh_dir, cfg.process.texturing.mesh_file)) and \
        io.is_non_zero_file(os.path.join(cfg.process.textured_mesh_dir, cfg.process.texturing.mtl_file)) and \
            len(glob(os.path.join(cfg.process.textured_mesh_dir, cfg.process.texturing.atlas_file))) > 0:
        validate['texturing'] = 'true'
    else:
        validate['texturing'] = 'false'
        all_valid = False

    # check segmentation
    # filename is mesh filename + segs extension
    segs_filename = os.path.splitext(cfg.process.texturing.mesh_file)[0] + (cfg.process.segmentation.segs_ext % (OmegaConf.to_object(cfg.process.segmentation.kthesh)[0]))
    segs_file = os.path.join(cfg.process.textured_mesh_dir, segs_filename)
    if io.is_non_zero_file(segs_file):
        validate['segmentation'] = 'true'
    else:
        validate['segmentation'] = 'false'
        all_valid = False
    
     # check render
    if io.is_non_zero_file(os.path.join(cfg.process.output_dir, cfg.process.scan_name + cfg.process.render.low_res_ply)) and \
        io.is_non_zero_file(os.path.join(cfg.process.output_dir, cfg.process.scan_name + cfg.process.render.low_res_obj)):
        validate['render'] = 'true'
    else:
        validate['render'] = 'false'
        all_valid = False

    # check thumbnail
    if io.is_non_zero_file(os.path.join(cfg.process.output_dir, cfg.process.scan_name + cfg.process.thumbnail.thumbnail_ext)) and \
        io.is_non_zero_file(os.path.join(cfg.process.output_dir, cfg.process.scan_name + cfg.process.thumbnail.preview_ext)):
        validate['thumbnail'] = 'true'
    else:
        validate['thumbnail'] = 'false'
        all_valid = False

    # check alignpairs
    if io.is_non_zero_file(os.path.join(cfg.process.output_dir, cfg.process.scan_name + cfg.process.align.align_ext)):
        validate['alignpairs'] = 'true'
    else:
        validate['alignpairs'] = 'false'

    if all_valid:
        validate['allValid'] = 'true'
    else:
        validate['allValid'] = 'false'
        
    return validate
    

def process_scan_dir_basic(path, name, cfg, proc_type):
    # Check if already processed
    processed_file = os.path.join(path, cfg.process.processed_file)
    validate = {}
    if io.is_non_zero_file(processed_file):
        validate = util.read_properties(processed_file, log)
        if not cfg.get('overwrite') and validate.get('allValid', 'false') == 'true':
            return 'Scan at %s already fully processed' % path

    # parse input and output paths
    cfg.process.scan_dir = os.path.abspath(path)
    cfg.process.scan_name = name
    scan_basename = os.path.join(cfg.process.scan_dir, cfg.process.scan_name)
    cfg.process.meta_file = scan_basename + '.json'
    cfg.process.color_stream = scan_basename + '.mp4'
    cfg.process.depth_stream = scan_basename + '.depth.zlib'
    cfg.process.confidence_stream = scan_basename + '.confidence.zlib'
    cfg.process.camera_file = scan_basename + '.jsonl'

    cfg.process.output_dir = os.path.join(cfg.process.scan_dir, cfg.process.output_folder)
    cfg.process.color_dir = os.path.join(cfg.process.output_dir, cfg.process.decode.color_folder)
    cfg.process.depth_dir = os.path.join(cfg.process.output_dir, cfg.process.decode.depth_folder)
    cfg.process.textured_mesh_dir = os.path.join(cfg.process.output_dir, cfg.process.texturing.result_folder)

    cfg.process.mesh_filename = cfg.reconstruction.output.mesh_filename
    if "%s" in cfg.process.mesh_filename:
        cfg.process.mesh_filename = cfg.reconstruction.output.mesh_filename % cfg.process.scan_name

    cfg.process.decimated_mesh_filename = cfg.reconstruction.output.decimated_mesh_filename
    if "%s" in cfg.process.decimated_mesh_filename:
        cfg.process.decimated_mesh_filename = cfg.reconstruction.output.decimated_mesh_filename % cfg.process.scan_name

    cfg.process.mesh_alignment_filename = cfg.reconstruction.output.mesh_alignment_filename
    if "%s" in cfg.process.mesh_alignment_filename:
        cfg.process.mesh_alignment_filename = cfg.reconstruction.output.mesh_alignment_filename % cfg.process.scan_name
    
    io.ensure_dir_exists(cfg.process.output_dir)

    if proc_type == ProcessStage.PRELIMINARY:
        ret = process_preliminary(cfg, validate)
    elif proc_type == ProcessStage.EXTRA:
        ret = process_extra(cfg, validate)

    tag = "preliminary" if proc_type == ProcessStage.PRELIMINARY else "extra"
    with open(os.path.join(processed_file), 'w+') as f:
        content = validate_process(cfg)
        for key, val in content.items():
            line = key + "=" + val + '\n'
            f.write(line)
    
    return 'Scan at %s %s processed' % (path, tag)


def get_good_candidates(cfg):
    scans_list = get_web_scans_list(cfg.process.align.scans_list_url)
    candidate_ids = []
    for i, scan_dict in enumerate(scans_list):
        scan_group = scan_dict.get('group', '')
        if scan_group == 'staging' or scan_group == 'checked':
            candidate_ids.append(scan_dict.get('id'))

    return candidate_ids


def process_scan_dir_batch(dirname, config):
    # For now, assume one directory deep (can use os.walk() to recursively descend
    entries = glob(dirname + '/*/')
    entries, _ = io.sorted_alphanum(entries)
    good_candidates = get_good_candidates(config)
    for dir in entries:
        name = os.path.relpath(dir, dirname)
        if name in good_candidates:
            log.info('Processing ' + dir + ' ' + name)
            process_scan_dir(dir, name, config, ProcessStage.PRELIMINARY)
            process_scan_dir(dir, name, config, ProcessStage.EXTRA)
        else:
            log.info('Skip bad scan' + dir + ' ' + name)


def process_scan_dirs(dirs, config):
    # For now, assume one directory deep (can use os.walk() to recursively descend
    good_candidates = get_good_candidates(config)
    for dir in dirs:
        name = os.path.relpath(dir, os.path.join(dir, '..'))
        if name in good_candidates:
            log.info('Processing ' + dir + ' ' + name)
            process_scan_dir(dir, name, config, ProcessStage.PRELIMINARY)
            process_scan_dir(dir, name, config, ProcessStage.EXTRA)
        else:
            log.info('Skip bad scan' + dir + ' ' + name)


@hydra.main(config_path="../config", config_name="config")
def main(cfg : DictConfig):
    if not os.path.isabs(cfg.process.staging_dir):
        cfg.process.staging_dir = os.path.join(get_original_cwd(), cfg.process.staging_dir)

    if not os.path.isabs(cfg.process.input_path):
        cfg.process.input_path = os.path.join(get_original_cwd(), cfg.process.input_path)
    
    if not os.path.isabs(cfg.process.scripts_path):
        cfg.process.scripts_path = os.path.join(get_original_cwd(), cfg.process.scripts_path)

    if not os.path.isabs(cfg.process.reconstruction_path):
        cfg.process.reconstruction_path = os.path.join(get_original_cwd(), cfg.process.reconstruction_path)

    actions = OmegaConf.to_object(cfg.process.actions)
    action_dict = dict.fromkeys(actions, True)
    actions = OmegaConf.create(action_dict)
    # allow add new keys
    OmegaConf.set_struct(cfg, False)
    cfg = OmegaConf.merge(cfg, actions)
    cfg.overwrite = cfg.process.overwrite

    # hydra by default is on another directory
    cwd = os.getcwd()
    cfg.dump_cfg_path = cwd
    os.chdir(get_original_cwd())
    if os.path.isdir(cfg.process.input_path):
        if cfg.process.batch_process:
            process_scan_dir_batch(cfg.process.input_path, cfg)
        else:
            name = os.path.relpath(cfg.process.input_path, os.path.join(cfg.process.input_path, '..'))
            process_scan_dir(cfg.process.input_path, name, cfg, ProcessStage.PRELIMINARY)
            process_scan_dir(cfg.process.input_path, name, cfg, ProcessStage.EXTRA)
    elif os.path.isfile(cfg.process.input_path):
        dirs = util.readlines(cfg.process.input_path)
        process_scan_dirs(dirs, cfg)
    else:
        log.error('Please specify directory or file as input')
    os.chdir(cwd)


if __name__ == "__main__":
    main()
