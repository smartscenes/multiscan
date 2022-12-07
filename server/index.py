#!/usr/bin/env python
#
# Indexes scans into csv file
# Run with ./index.py (or python index.py on Windows)

import argparse
import csv
import json
import logging
import os
import re
import sys
from glob import glob

from six import string_types

from multiscan.utils import io

import compute_timings as timings
import util

DATA_OUTPUTS = 'outputs'

FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger('index')
log.setLevel(logging.INFO)

# For matching 2016-07-01_04-29-28
DATE_RE = re.compile(r"\d\d\d\d\d\d\d\dT\d\d\d\d\d\d")
# For matching sceneLabel with end digit (and stripping it to get a sceneName)
SCENELABEL_RE = re.compile(r'^(.*?)[_-]?\d\s*$')


def index_all_recursive(dirname, writer, args):
    indexed = 0
    for root, dirs, files in os.walk(dirname):
        for name in dirs:
            dir = os.path.join(root, name)
            if has_scan(dir):
                subdir = os.path.relpath(dir, dirname)
                indexed += index_single(dir, subdir, writer, args)
            else:
                log.warning('Skipping directory without scan: ' + dir)
    log.info('Indexed ' + str(indexed) + ' scans')


def index_all(dirname, writer, args):
    entries = glob(dirname + '/*/')
    indexed = 0
    for dir in entries:
        dir = strip_dirname(dir)
        subdir = os.path.relpath(dir, dirname)
        indexed += index_single(dir, subdir, writer, args)
    log.info('Indexed ' + str(indexed) + ' scans')


def index_single(dirname, subdir, writer, args):
    # Indexes a single multiscan entry (stored in one directory)
    #  by extract the metadata and appending it to the writer
    meta = extract_meta(dirname, subdir, args)
    if meta:
        writer(meta)
        return 1
    else:
        log.warning('Skipping directory without good scan: ' + dirname)
        return 0


def convert_data(data, meta):
    output = None
    if isinstance(data, dict):
        output = {}
        for key, value in data.items():
            output[key] = convert_data(value, meta)
    elif isinstance(data, list):
        output = []
        for value in data:
            output.append(convert_data(value, meta))
    elif isinstance(data, string_types):
        output = data.replace('${id}', meta['id'])
    else:
        output = data

    return output


def has_scan(dirname):
    dirname = strip_dirname(dirname)
    id = os.path.basename(dirname)
    # If any of these files exists, this directory is likely to be a scan
    files = [id + '.json', id + '.confidence.zlib',
             id + '.depth.zlib', id + '.mp4', id + '.jsonl']
    count = 0
    for file in files:
        if io.is_non_zero_file(os.path.join(dirname, file)):
            count += 1
    if count >= len(files) - 1:
        return True
    return False


def check_files(filesByName, files, checkAny=False):
    nFilesOk = 0
    all_files = list(filesByName.keys())
    
    for file in files:
        if file.find('*') != -1 or file.find('+') != -1:
            file_pattern = re.compile(file)
            matched_files = [fi for fi in all_files if file_pattern.match(fi)]
        else:
            matched_files = [file]
        for mf in matched_files:
            f = filesByName.get(mf)
            if f and f.get('size') > 0:
                nFilesOk += 1  # OK
    if checkAny:
        return nFilesOk > 0
    else:
        return nFilesOk >= len(files)

def check_stages_impl(stages, meta, times=None):
    filesByName = dict((f.get('name'), f) for f in meta.get('files'))
    stageStatuses = []
    lastAllOk = ''
    failed = False
    for stage in stages:
        if times is not None:
            timeRec = timings.getRecord(
                times, stage.get('name'), stage.get('substeps'))
        else:
            timeRec = None

        ok = None  # Don't know if okay
        if stage.get('output'):
            outputOk = check_files(filesByName, stage.get(
                'output'), stage.get('outputCheck') == 'any')
            if outputOk:
                ok = True
        if ok and stage.get('checks'):
            for k, v in stage.get('checks').items():
                if meta.get(k) != v:
                    ok = False
                    break

        # Check input
        if stage.get('force'):
            inputOk = True
        elif stage.get('input') and times is not None:
            inputOk = check_files(filesByName, stage.get('input'))
        else:
            inputOk = None

        outdated = False
        if ok is None:
            if inputOk and not stage.get('optional'):
                ok = False
        else:
            if inputOk:
                # Check if output is out of date
                inputs = [filesByName.get(name)
                            for name in stage.get('input')]
                inputs = [f for f in inputs if f is not None]
                lastModifiedInput = util.last_modified(inputs)
                lastModifiedMillis = lastModifiedInput.get(
                    'modifiedAtMillis')
                outputs = [filesByName.get(name)
                            for name in stage.get('output')]
                outputs = [f for f in outputs if f is not None]
                outdated = any(f.get('modifiedAtMillis') <
                                lastModifiedMillis for f in outputs)

        status = {'name': stage.get('name')}
        if timeRec is not None:
            status['secs'] = timeRec['secs']
            status['time'] = timeRec['time']
        if outdated:
            status['outdated'] = True
        if ok is not None:
            status['ok'] = ok
        stageStatuses.append(status)
        if not failed:
            if ok:
                lastAllOk = stage.get('name')
            elif not stage.get('optional'):
                failed = True
    return stageStatuses, lastAllOk

def check_stages(stages_data, meta, times=None):
    converted = convert_data(stages_data, meta)
    stages = converted.get('stages')
    if meta.get('files'):
        stageStatuses, lastAllOk = check_stages_impl(stages, meta, times)
        
        meta['stages'] = stageStatuses
        meta['lastOkStage'] = lastAllOk


def parse_meta(fpath, log):
    meta = {}
    with open(fpath, 'r') as f:
        data = json.load(f)
        # log.info(data)
        try:
            meta['deviceId'] = data['device']['id']
            meta['group'] = 'staging'
            meta['deviceName'] = data['device']['name']
            meta['sceneType'] = data['scene']['type']
            meta['userName'] = data['user']['name']
            meta['numColorFrames'] = data['streams'][0].get('number_of_frames', 0)
            meta['numDepthFrames'] = data['streams'][1].get('number_of_frames', 0)
        except Exception as e:
            print(e)
    return meta


def strip_dirname(dirname):
    # Make sure dirname don't end in '/', otherwise our poor basename is not going to work well
    return dirname.rstrip('/').rstrip('\\')


def extract_meta(dirname, subdir, args):
    source = args.get('source')
    datasets = args.get('datasets')

    # Make sure dirname don't end in '/', otherwise our poor basename is not going to work well
    dirname = strip_dirname(dirname)

    # Extract metadata from csv and create a record

    # First check if okay by looking into processed.txt
    processedFile = os.path.join(dirname, 'processed.txt')
    processed = None
    if io.is_non_zero_file(processedFile):
        processed = util.read_properties(processedFile, log)
        if not processed:
            if not args.get('includeAll'):
                return False  # NOT ACCEPTABLE
    else:
        if not args.get('includeAll'):
            return False  # NOT ACCEPTABLE

    # Process log
    times = None
    processLog = os.path.join(dirname, 'process.log')
    if os.path.isfile(processLog):
        times = timings.computeTimings(processLog)

    # Take dirname and extract the final string as the id
    id = os.path.basename(dirname)
    if subdir is None:
        subdir = id

    meta1 = {
        'fullId': source + '.' + id,
        'id': id,
        'source': source,
        'datasets': datasets,
        'path': subdir
    }
    if times is not None:
        total = timings.getTotal(times)
        meta1['totalProcessingSecs'] = total.get('secs')
        meta1['totalProcessingTime'] = total.get('time')
    # Extract create time from id matching: 20160701T042928
    date_match = DATE_RE.search(id)
    if date_match:
        createdAt = date_match.group(0)
        # Reformat to be in ISO8601 format
        meta1['createdAt'] = createdAt[0:4] + '-' + createdAt[4:6] + '-' + createdAt[6:8] \
            + 'T' + createdAt[9:11] + ':' + \
            createdAt[11:13] + ':' + createdAt[13:15]

    # Look for dirname/id.txt and extract fields into our meta
    # if there is txt file, read it and append to metadata record
    metafile = dirname + '/' + id + '.json'
    if io.is_non_zero_file(metafile):
        # Read in txt as dictionary
        # meta = util.read_properties(metafile, log)
        meta = parse_meta(metafile, log)
        # log.info(meta)
    else:
        meta = {}
    # go through files and find last time as updatedAt time for scan

    # Take our basic info and merge it into meta (overwriting what maybe there)
    if processed:
        meta.update(processed)
    meta.update(meta1)

    # Check what files we have
    meta['files'] = util.list_files(dirname, recursive=True)
    lastModified = util.last_modified(meta['files'])
    if lastModified:
        meta['updatedAt'] = util.millis_to_iso(
            lastModified.get('modifiedAtMillis'))

    # Check what stage we are in
    # NOTE: This requires meta to be filled in with id and files!!!
    if args.get('stages'):
        check_stages(args.get('stages'), meta, times)

    # Check if we have a ply file and how big it is
    filebase = id  # + '_vh_clean_2' if args.get('checkCleaned') else id
    plyfile = dirname + '/' + filebase + '.ply'
    plyfile2 = os.path.join(dirname, DATA_OUTPUTS, filebase + '.ply')
    plyfileSize = io.filesize(plyfile) or io.filesize(plyfile2)
    meta['hasCleaned'] = args.get('checkCleaned') and plyfileSize > 0
    if plyfileSize > 0:
        meta['fileType'] = 'ply'
        meta['fileSize'] = plyfileSize

    # Check if we have a png file
    pngfile = dirname + '/' + filebase + '_thumb.jpg'
    pngfileSize = io.filesize(pngfile)
    meta['hasScreenshot'] = pngfileSize > 0

    # Check if we have a thumbnail file
    pngfile = dirname + '/' + filebase + '_ply_thumb_low.png'
    pngfileSize = io.filesize(pngfile)
    meta['hasThumbnail'] = pngfileSize > 0
    # Check if we have a textured mesh thumbnail file
    pngfile = dirname + '/' + filebase + '_obj_thumb_low.png'
    pngfileSize = io.filesize(pngfile)
    meta['hasObjThumbnail'] = pngfileSize > 0
    # check if we have a textured mesh thumbnail file from mvs-texturing
    pngfile = os.path.join(dirname, DATA_OUTPUTS, filebase + '_obj_thumb_low.png')
    pngfileSize = io.filesize(pngfile)
    meta['hasObjThumbnailMVS'] = pngfileSize > 0

    if source == 'nyuv2' and not meta.get('sceneType'):
        idParts = meta.get('id').split('_')
        meta['sceneType'] = '_'.join(idParts[0:len(idParts) - 1])

    if meta.get('sceneLabel'):
        # Derive sceneName from sceneLabel
        sceneLabel = meta.get('sceneLabel')
        match = SCENELABEL_RE.match(sceneLabel)
        meta['sceneName'] = match.group(1) if match else sceneLabel

    return meta


def loadJson(infile):
    return json.load(infile)


def saveJson(data, out):
    json.dump(data, out, indent=1, separators=(',', ': '))


def loadCsv(infile):
    reader = csv.DictReader(infile)
    rows = {}
    for row in reader:
        rows[row['id']] = row
    return rows


def saveCsv(data, csvfile):
    # Index and output
    fieldnames = ['fullId', 'source', 'id', 'datasets',
                  'valid', 'aligned', 
                  'hasScreenshot', 'hasThumbnail', 'hasObjThumbnail', 'hasObjThumbnailMVS', 'hasCleaned',
                  'fileType', 'fileSize',
                  'sceneLabel', 'sceneName', 'sceneType', 'group',
                  'deviceId', 'deviceName', 'userName',
                  'numDepthFrames', 'numColorFrames', 'numIMUmeasurements',
                  'lastOkStage', 'createdAt', 'updatedAt', 'path']
    writer = csv.DictWriter(
        csvfile, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for k, v in data.items():
        writer.writerow(v)


def index(args):
    if args.get('stagesFile'):
        with open(args.get('stagesFile')) as json_data:
            args['stages'] = json.load(json_data)
    if args.get('format') == 'json':
        return indexAndSave(args, loadJson, saveJson)
    else:
        return indexAndSave(args, loadCsv, saveCsv)


def assignItem(m, id, entry):
    m[id] = entry


def indexAndSave(args, loadFn, saveFn):
    if args.get('output'):
        print('Indexing ' + args.get('input') + ' to ' + args.get('output'))

    # index into memory
    rows = {}
    if args.get('single'):
        subdir = None
        if args.get('root'):
            subdir = os.path.relpath(args.get('input'), args.get('root'))
        else:
            subdir = os.path.basename(args.get('input'))
        index_single(args.get('input'), subdir,
                     lambda r: assignItem(rows, r['id'], r), args)
    elif args.get('recursive'):
        index_all_recursive(args.get('input'),
                            lambda r: assignItem(rows, r['id'], r), args)
    else:
        index_all(args.get('input'), lambda r: assignItem(
            rows, r['id'], r), args)

    # output
    allRows = rows
    if args.get('output'):
        # read existing if there
        isNonEmpty = io.is_non_zero_file(args.get('output'))
        if args.get('append') and isNonEmpty:
            with open(args.get('output')) as data:
                existing = loadFn(data)
                # combine old with new
                allRows = existing.copy()
                allRows.update(rows)
        output = open(args.get('output'), 'w')
    else:
        output = sys.stdout

    # dump output
    saveFn(allRows, output)

    output.flush()
    if args.get('output'):
        output.close()
    return rows

# TODO: switch to use hydra
def main():
    scriptpath = os.path.dirname(os.path.realpath(__file__))
    # Argument processing
    parser = argparse.ArgumentParser(description='Index scans!!!')
    parser.add_argument('-i', '--input', dest='input', action='store',
                        help='Input directory')
    parser.add_argument('-o', '--output', dest='output', action='store',
                        help='Output CSV filename')
    parser.add_argument('-s', '--single', dest='single', action='store_true',
                        default=False,
                        help='Input directory points to a single entry')
    parser.add_argument('-a', '--append', dest='append', action='store_true',
                        default=False,
                        help='Append to output')
    parser.add_argument('--all', dest='includeAll', action='store_true',
                        default=False,
                        help='Include all scans (including unprocessed scans)')
    # TODO: Remove this option at some point
    parser.add_argument('--nonrecursive', dest='recursive', action='store_false',
                        default=True,
                        help='Non-recursive processing of directory')
    parser.add_argument('--solr', dest='solr', action='store',
                        default='https://<SERVER>/models3d/solr/',
                        help='Solr url for updating the solr index')
    parser.add_argument('--datasets', dest='datasets', action='store',
                        default='MultiScan',
                        help='Name of dataset')
    parser.add_argument('--stages', dest='stagesFile', action='store',
                        default=os.path.join(
                            scriptpath, 'config/scan_stages.json'),
                        help='File specifying scan stages')
    parser.add_argument('--source', dest='source', action='store',
                        default='scan',
                        help='Source to use for fullId')
    parser.add_argument('--format', dest='format', action='store',
                        default='csv', choices=['csv', 'json'],
                        help='Format to use for output')
    parser.add_argument('--checkBasic', dest='checkCleaned', action='store_false',
                        default=True,
                        help='Check for basic ply or the cleaned ply')

    args = parser.parse_args()
    index(vars(args))


if __name__ == "__main__":
    main()
