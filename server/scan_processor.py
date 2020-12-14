#!/usr/bin/env python
#
# Process scans from ipad and runs recons pipeline
# Run with ./scan_processor.py (or python scan_processor.py on Windows)

import argparse
import os
import logging

import util
import traceback
from glob import glob
import config as cfg
import json

SCRIPT_DIR = util.getScriptPath()
PROCESSES = ['convert', 'recons', 'photogrammetry', 'render', 'thumbnail']

# where devices information is stored
DEVICES_DIR = os.path.join(cfg.DATA_DIR, 'devices')
DEVICES_CSV = os.path.join(DEVICES_DIR, 'devices.csv')
# ffmpeg to call for converting iPad raw files to image files
DECODE_DIR = cfg.DECODE_DIR
DECODE_BIN = os.path.join(DECODE_DIR, '')
# module to call for reconstruction
RECONS_DIR = os.path.join(cfg.TOOLS_DIR, cfg.RECONS_DIR)
RECONS_BIN = os.path.join(RECONS_DIR, '')
# module to call for photogrammetry reconstruction
PHOTOGRAMMETRY_DIR = os.path.join(cfg.TOOLS_DIR, cfg.PHOTOGRAMMETRY_DIR)
PHOTOGRAMMETRY_BIN = os.path.join(PHOTOGRAMMETRY_DIR, '')

CONVERT_MP4_TO_THUMBNAIL_BIN = os.path.join(SCRIPT_DIR, 'scripts', 'mp4_thumbnail.sh')

CMD_ARGS = []
if os.name == 'nt':
    GIT_BASH = 'C:\\Program Files\\Git\\bin\\bash.exe'
    CMD_ARGS = [GIT_BASH]

FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
formatter = logging.Formatter(FORMAT)
logging.basicConfig(format=FORMAT)
log = logging.getLogger('scan_processor')
log.setLevel(logging.INFO)

TEST_MODE = False


def decode_color(color_stream, color_out, desc, skip=1):
    try:
        ret = 0
        if os.path.isfile(color_stream):
            util.make_clean_folder(color_out)
            ret = util.call(['ffmpeg', '-i', color_stream, '-vf', f'select=not(mod(n\\,{skip}))',
                             '-vsync', 'vfr', '-start_number', '0',
                             os.path.join(color_out, '%d.png')], log, desc=desc)

        log.info(f'Decoding color stream is ended, return code {ret}')
        return ret
    except Exception as e:
        log.error(traceback.format_exc())
        raise e


def decode_depth(depth_stream, confidence_stream, depth_out, desc, skip=1):
    ret = 0
    try:
        if os.path.isfile(depth_stream):
            util.make_clean_folder(depth_out)
            env = os.environ.copy()
            env['PYTHONPATH'] = ":".join(DECODE_DIR)
            if os.path.isfile(confidence_stream):
                ret = util.call(['python', 'depth2png.py', '-in', depth_stream, '-in_confi', confidence_stream, '-W', '256', '-H', '192', '-S', str(skip),
                                '-L', '1', '--filter', '-o', depth_out], log, DECODE_DIR, env=env, desc=desc)
            else:
                ret = util.call(['python', 'depth2png.py', '-in', depth_stream, '-W', '256', '-H', '192', '-S', str(skip),
                             '-o', depth_out], log, DECODE_DIR, env=env, desc=desc)
        log.info(f'Decoding depth stream is ended, return code {ret}')
        return ret
    except Exception as e:
        log.error(traceback.format_exc())
        raise e

def update_config(config):
    if config.get('all'):
        for name in PROCESSES:
            config[name] = True
    else: 
        if config.get('from'):
            fromSeen = False
            for name in PROCESSES:
                fromSeen = fromSeen or name == config['from']
                config[name] = fromSeen
        if config.get('actions'):
            actions = json.loads(config['actions'])
            for action in actions:
                if action in PROCESSES:
                    config[action] = True
    
    return config


def process_scan_dir(path, name, config):
    # Check if valid scan dir
    namebase = os.path.join(path, name)
    validNovh = os.path.isfile(namebase + ".mp4")
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
        msg = process_scan_dir_basic(path, name, config)
        log.info(msg)
    finally:
        log.removeHandler(fh)
        fh.close()
    return msg


def process_scan_dir_basic(path, name, config):
    # Check if already processed
    if not config.get('overwrite'):
        processedFile = os.path.join(path, 'processed.txt')
        if os.path.isfile(processedFile):
            return 'Scan at %s already processed' % path

    # Convert to sens file
    path = os.path.abspath(path)
    filename = os.path.basename(path)
    outbase = os.path.join(cfg.DATA_DIR, filename)
    outbase = os.path.abspath(outbase)
    meta_file = os.path.join(path, filename + '.json')
    color_stream = os.path.join(path, filename + '.mp4')
    depth_stream = os.path.join(path, filename + '.depth.zlib')
    confidence_stream = os.path.join(path, filename + '.confidence.zlib')
    camera_file = os.path.join(path, filename + '.jsonl')
    # intrinsic_file = os.path.join(path, filename + '.intr')
    color_dir = os.path.join(outbase, cfg.COLOR_FOLDER)
    depth_dir = os.path.join(outbase, cfg.DEPTH_FOLDER)
    util.ensure_dir_exists(outbase)

    color_exists = os.path.exists(color_dir)
    depth_exists = os.path.exists(depth_dir)
    with open(meta_file, 'r') as f:
        meta = json.load(f)

    # TODO: not utilize return value yet
    ret = 0
    # Decode video to frames
    if config.get('convert'):
        if config.get('overwrite') or (not color_exists or not depth_exists):
            skip_frames = 2
            ret = decode_color(color_stream, color_dir, 'convert color', skip_frames)
            if ret != 0:
                return 'Scan at %s aborted: decode color stream failed' % path
            ret = decode_depth(depth_stream, confidence_stream, depth_dir, 'convert depth', skip_frames)
            if ret != 0:
                return 'Scan at %s aborted: decode depth stream failed' % path

            color_frames = util.get_file_list(color_dir, '.png')
            depth_frames = util.get_file_list(depth_dir, '.png')
            if len(color_frames) == 0:
                return 'Scan at %s aborted: no decoded color images (convert failed)' % path
            if len(depth_frames) == 0:
                return 'Scan at %s aborted: no decoded depth images (convert failed)' % path
            if len(color_frames) != len(depth_frames):
                return 'Scan at %s aborted: the number of decoded depth images does not match color ' \
                    'images (convert failed)' % path
        else:
            log.info('skipping convert')

    # Open3D Reconstruction
    if config.get('recons'):
        env = os.environ.copy()
        env['PYTHONPATH'] = ":".join(RECONS_DIR)
        log.info(f'Start processing using open3d integration')
        ret = util.call(['python', 'main.py', '-inc', color_stream, '-ind', depth_stream,
                        '-inm', meta_file, '-inp', camera_file, '-inconfi', confidence_stream,
                        #  '-num_cpu', '8',
                        '-inmem', '-s', '2', '-thresh', '0.05', '-voxel', '5.0', '-trunc', '0.08',
                        '-o', os.path.join(outbase, cfg.RECONS_RESULT_DIR)],
                        log, RECONS_DIR, env=env)

    # Meshroom Reconstruction
    if config.get('photogrammetry'):
        if config.get('overwrite') or not color_exists:
            if config.get('convert'):
                skip_frames = 10
                ret = decode_color(color_stream, color_dir, 'convert color', skip_frames)
                if ret != 0:
                    return 'Scan at %s aborted: decode color stream failed' % path
        else:
            log.info('skipping convert')

        color_frames = util.get_file_list(color_dir, '.png')
        if len(color_frames) == 0:
            return 'Scan at %s aborted: no decoded color images (convert failed)' % path

        log.info(f'Start processing using meshroom photogrammetry')
        ret = util.call(['./meshroom_photogrammetry', '--input', color_dir, '--output',
                         os.path.join(outbase, cfg.PHOTOGRAMMETRY_RESULT_DIR)], log, PHOTOGRAMMETRY_DIR)

    if config.get('render'):
        thumb_ext = '_o3d_thumb.png'
        mesh_file = os.path.join(path, filename + '.ply')
        thumb_path = os.path.join(path, filename + thumb_ext)
        if util.is_non_zero_file(mesh_file):
            if not util.is_non_zero_file(thumb_path) or config.get('overwrite'):
                log.info(f'Start creating rendered mesh thumbnail image')
                env = os.environ.copy()
                env['PYTHONPATH'] = ":".join(DECODE_DIR)
                ret = util.call(['python', 'render.py', '-i', mesh_file, '-w', '200', '-o', thumb_path],
                                log, DECODE_DIR, env=env, desc='open3d mesh render thumb image')


    if config.get('thumbnail'):
        if config.get('overwrite'):
            ret = util.call(CMD_ARGS + [CONVERT_MP4_TO_THUMBNAIL_BIN, path], log, desc='mp4-thumbnail')
        else:
            ret = util.call(CMD_ARGS + [CONVERT_MP4_TO_THUMBNAIL_BIN, '--skip-done', path], log, desc='mp4-thumbnail')

    with open(os.path.join(outbase, 'processed.txt'), 'w+') as f:
        content = 'valid = true'
        f.write(content)

    return 'Scan at %s processed' % path


def process_scan_dir_batch(dirname, config):
    # For now, assume one directory deep (can use os.walk() to recursively descend
    entries = glob(dirname + '/*/')
    for dir in entries:
        name = os.path.relpath(dir, dirname)
        log.info('Processing ' + dir + ' ' + name)
        process_scan_dir(dir, name, config)


def process_scan_dirs(dirs, config):
    # For now, assume one directory deep (can use os.walk() to recursively descend
    for dir in dirs:
        name = os.path.relpath(dir, dir + '/..')
        log.info('Processing ' + dir + ' ' + name)
        process_scan_dir(dir, name, config)


def main():
    # Argument processing
    parser = argparse.ArgumentParser(description='Process scans!!!')
    parser.add_argument('-i', '--input', dest='input', action='store',
                        required=True,
                        help='Input directory or list of directories (if file)')
    parser.add_argument('-b', '--batch', dest='batch', action='store_true',
                        default=False,
                        help='Batch processing of input directory')
    parser.add_argument('--from', dest='from', action='store',
                        default='convert',
                        choices=PROCESSES,
                        help='Which command to start from')
    parser.add_argument('--action', dest='actions', action='append',
                        choices=PROCESSES,
                        help='What actions to do')
    parser.add_argument('--overwrite', dest='overwrite', action='store_true', default=False,
                        help='Overwrite existing files')
    parser.add_argument('--novh', dest='novh', action='store_true', default=False,
                        help='Remove _vh suffixes')
    parser.add_argument('--test', dest='test', action='store_true', default=False,
                        help='Test pipeline commands without executing them')

    args = parser.parse_args()
    config = {}
    if args.overwrite:
        config['overwrite'] = True
    if args.novh:
        config['novh'] = True
    if args.actions:
        for action in args.actions:
            config[action] = True
    else:
        config = update_config(vars(args))

    global TEST_MODE
    TEST_MODE = args.test
    util.setCallTestMode(args.test)

    if os.path.isdir(args.input):
        if args.batch:
            process_scan_dir_batch(args.input, config)
        else:
            name = os.path.relpath(args.input, args.input + '/..')
            process_scan_dir(args.input, name, config)
    elif os.path.isfile(args.input):
        dirs = util.readlines(args.input)
        process_scan_dirs(dirs, config)
    else:
        print('Please specify directory or file as input')


if __name__ == "__main__":
    main()
