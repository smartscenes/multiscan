import datetime
import glob
import os
import re
import traceback

from enum import Enum
from flask import jsonify

from multiscan.utils import io


class ProcessStage(Enum):
    PRELIMINARY = 0
    EXTRA = 1


class TexturingMethod(Enum):
    MVS_TEXTURING = 0
    MESHROOM = 1


def read_properties(fpath, log):
    # Read in txt as dictionary
    try:
        lines = filter(None, (line.rstrip() for line in open(fpath)))
        props = dict(line.strip().split('=', 2) for line in lines)
        # Strip whitespace (can also do so by using regex (re) to split)
        props = {k.strip(): v.strip() for k, v in props.items()}
        return props
    except Exception as e:
        log.error('Error reading properties from ' + fpath)
        log.error(traceback.format_exc())
        return False


def list_files(dirname, recursive=False):
    # Get list of files in directory and their name, size, date
    dirname = os.path.abspath(dirname)
    if recursive:
        files = glob.glob(dirname + '/**/*', recursive = True)
    else:
        files = os.listdir(dirname)
    fileinfos = []
    for file in files:
        st = os.stat(os.path.join(dirname, file))
        mtimestr = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        name = re.sub(r'^' + dirname + '/+', '', file)
        fileinfos.append({
            'name': name,
            'size': st.st_size,
            'modifiedAt': mtimestr,
            'modifiedAtMillis': int(round(st.st_mtime * 1000))
        })
    return fileinfos


def last_modified(fileinfos):
    # Get the last modifiedAt string
    last = None
    for fileinfo in fileinfos:
        if last == None or fileinfo.get('modifiedAtMillis') > last.get('modifiedAtMillis'):
            last = fileinfo
    return last


def millis_to_iso(millis):
    # Return timestamp in ISO 8601
    mtimestr = datetime.datetime.fromtimestamp(millis / 1000.0).strftime('%Y-%m-%dT%H:%M:%S')
    return mtimestr


def secs_to_iso(secs):
    # Return timestamp in ISO 8601
    mtimestr = datetime.datetime.fromtimestamp(secs).strftime('%Y-%m-%dT%H:%M:%S')
    return mtimestr


def check_last_modified_newer(dirname, timestamp):
    fileinfos = list_files(dirname)
    last = last_modified(fileinfos)
    if last is not None:
        lastMs = last.get('modifiedAtMillis')
        # print('last modified is ' + str(lastMs) + ', request timestamp is ' + str(timestamp))
        return lastMs > timestamp
    else:
        return None


# Read lines and returns as list (ignores empty lines)
def readlines(input):
    lines = []
    with open(input) as x:
        for line in x:
            line = line.strip()
            if len(line):
                lines.append(line)
    return lines


# Returns a recursive directory tree for path (relative to base_dir)
def make_tree(base_dir, path):
    tree = dict(name=os.path.basename(path), relative_name=path.replace(base_dir, 'received'), children=[])
    try:
        lst = os.listdir(path)
    except OSError:
        pass  # ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            if os.path.isdir(fn):
                tree['children'].append(make_tree(base_dir, fn))
            else:
                st = os.stat(fn)
                mtimestr = datetime.datetime.fromtimestamp(st.st_mtime).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                tree['children'].append(dict(name=name, fileSize=io.natural_size(st.st_size), modifiedAt=mtimestr,
                                             relative_name=os.path.join(path.replace(base_dir, 'received'), name)))
    return tree


# Return 200 OK message
def ret_ok(message='ok'):
    rv = {}
    rv['message'] = message
    ok_resp = jsonify(rv)
    ok_resp.status_code = 200
    return ok_resp


# Simple error class
class Error(Exception):
    def __init__(self, message='', status_code=500):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        rv = {}
        rv['message'] = self.message
        return rv

    def to_json(self):
        return jsonify(self.to_dict())
