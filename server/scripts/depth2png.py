import argparse
import numpy as np
import cv2
import zlib
import tempfile
import os
import utils
import matplotlib.pyplot as plt

def configure(args):
    if not utils.file_exist(args.input, '.zlib'):
        utils.print_e(f'Input file {args.input} not exists')
        return False

    utils.make_clean_folder(args.output)
    if not utils.folder_exist(args.output):
        utils.print_e(f'Create result folder {args.output} failed')
        return False
    
    if args.output_confidence:
        utils.make_clean_folder(args.output_confidence)

        if not utils.folder_exist(args.output_confidence):
            utils.print_e(f'Create result folder {args.output} failed')
            return False

    if args.width < 1:
        utils.print_e(f'Width of frames must be positive integers')
        return False

    if args.height < 1:
        utils.print_e(f'Height of frames must be positive integers')
        return False

    return True


def get_num_frames(args, tmpfile):
    file_size = os.stat(tmpfile.name).st_size
    frame_size = args.width*args.height*2
    if args.num == None:
        num_frames = int(file_size/frame_size)
    else:
        num_frames = min(int(file_size/frame_size), args.num)
    
    return num_frames, frame_size

def decompress(args, depth=True):
    d = zlib.decompressobj(-zlib.MAX_WBITS)
    chuck_size=4096 * 4
    input = args.input if depth else args.input_confidence
    tmp = tempfile.NamedTemporaryFile(prefix=os.path.basename(input), dir=os.path.dirname(args.output), delete=False)
    utils.print_m('temp file name: '+tmp.name)

    with open(input, 'rb') as f:
        buffer=f.read(chuck_size)
        while buffer:
            outstr = d.decompress(buffer)
            tmp.write(outstr)
            buffer=f.read(chuck_size)

        tmp.write(d.flush())
        tmp.close()

    return tmp


def write_frames(args):
    tmp = decompress(args)
    confidence_filter = args.input_confidence and utils.file_exist(args.input_confidence)
    if confidence_filter:
        tmp_confi = decompress(args, False)
    num_frames, frame_size = get_num_frames(args, tmp)
    out_num = int(num_frames/args.step)
    utils.print_m(f'{out_num} frames are being extracted')
    count = 0
    for i in range(num_frames):
        if not i % args.step == 0:
            continue
        fp = np.memmap(tmp.name, dtype='float16', mode='r', shape=(args.height, args.width), offset=frame_size*i).copy()

        if args.filter and i > 0:
            fp_last = np.memmap(tmp.name, dtype='float16', mode='r', shape=(args.height, args.width), offset=frame_size*(i-1)).copy()
            delta = np.abs(fp_last - fp)
            fp[delta>args.threshold]=0
        if confidence_filter:
            fp_confi = np.memmap(tmp_confi.name, dtype='uint8', mode='r', shape=(args.height, args.width), offset=int(frame_size/2*i)).copy()
            fp[fp_confi<=args.level]=0

            # output color mapped confidence images
            if args.output_confidence:
                cm = plt.get_cmap('Reds', 4)
                color = cm(fp_confi+1)
                color *= 255
                color = color.astype('uint8')
                color = cv2.cvtColor(color, cv2.COLOR_RGBA2BGRA)
                cv2.imwrite(os.path.join(args.output_confidence, '{}.png'.format(count)), color)
        fp *= 1000
        fp = fp.astype('uint16')
        # Debug Only
        # fp = cv2.resize(fp, (1920, 1440))
        if args.mode == 0:
            cv2.imwrite(os.path.join(args.output, '{}.png'.format(count)), fp)
        elif args.mode == 1: # write color frames
            fp = np.memmap(tmp.name, dtype='float16', mode='r', shape=(args.height, args.width), offset=frame_size*i).copy()

            cm = plt.get_cmap('jet')
            color = cm(fp.astype('float')/4.0)
            color *= 255
            color = color.astype('uint8')
            color = cv2.cvtColor(color, cv2.COLOR_RGBA2BGRA)
            cv2.imwrite(os.path.join(args.output, '{}.png'.format(count)), color)
        elif args.mode == 2: # write gray frames
            gray = cv2.normalize(fp, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8UC1)
            cv2.imwrite(os.path.join(args.output, '{}.png'.format(count)), gray)
        else:
            utils.print_w(f'Mode {args.mode} is not supported yet')
        count += 1
    os.unlink(tmp.name)
    if confidence_filter:
        os.unlink(tmp_confi.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Decode depth stream!')
    parser.add_argument('-in', '--input', dest='input', type=str, action='store', required=True,
                        help='Input depth stream zlib file')
    parser.add_argument('-in_confi', '--input_confidence', dest='input_confidence', type=str, action='store', required=False,
                        help='Input confidence stream zlib file')
    parser.add_argument('-W', '--width', dest='width', type=int, default=256, action='store', required=False,
                        help='Width of each frame')
    parser.add_argument('-H', '--height', dest='height', type=int, default=192, action='store', required=False,
                        help='Height of each frame')
    parser.add_argument('-N', '--num', dest='num', type=int, action='store', required=False,
                        help='Totoal number of frames')
    parser.add_argument('-M', '--mode', dest='mode', type=int, default=0, action='store', required=False,
                        help='Mode of processing the zlib depth stream')
    parser.add_argument('-S', '--step', dest='step', type=int, default=1, action='store', required=False,
                        help='Step size of skipping poses')
    parser.add_argument('-TH', '--threshold', dest='threshold', type=float, default=0.05, action='store', required=False,
                        help='Threshold for maximum depth delta difference')
    parser.add_argument('-F', '--filter', dest='filter', default=False, action='store_true', required=False,
                        help='Filter out points with large frame to frame delta')
    parser.add_argument('-L', '--level', dest='level', type=int, default=1, action='store', required=False,
                        help='Only consider points with confident greater than threshold')
    parser.add_argument('-o', '--output', dest='output', type=str, action='store', required=True,
                        help='Output directory of decoding results')
    parser.add_argument('-o_confi', '--output_confidence', dest='output_confidence', type=str, action='store', required=False,
                        help='Output directory of confidence maps')

    args = parser.parse_args()

    if not configure(args):
        exit(0)

    write_frames(args)
