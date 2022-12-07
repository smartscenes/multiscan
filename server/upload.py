#!/usr/bin/env python
#
# Install dependencies using install_deps.sh
# Run using start_upload_server.sh
#
# To mimic an upload from the iPad app use this curl command:
# curl -v -X PUT -H "FILE_NAME: test.mp4" --data-binary "@<path_to_some_file>" -H "Content-Type: application/ipad_scanner_data" "http://localhost:8000/upload"
# curl -v "localhost:8000/verify?filename=<base_file_name>&checksum=<check_sum>"

import json
import logging
import os
import shutil
import threading
import traceback
import multiprocessing

from urllib.error import URLError
from urllib.parse import unquote, urlencode
from urllib.request import urlopen

from flask import Flask, request, render_template_string, send_from_directory
from werkzeug.utils import secure_filename

import hydra
from hydra.utils import get_original_cwd
from omegaconf import DictConfig, OmegaConf

from configparser import ConfigParser

import util
from multiscan.utils import io

app = Flask(__name__)

log = logging.getLogger('scanner-ipad-server')

config = OmegaConf.load(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../config/config.yaml'))

@app.errorhandler(util.Error)
def handle_error(error):
    response = error.to_json()
    response.status_code = error.status_code
    return response


@app.before_request
def log_request_headers():
    log.info('Got request: %s', request.headers)


@app.after_request
def log_request_response(response):
    log.info('Got response: %s', response)
    return response


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in config.upload.allowed_extensions


# returns whether scan completely uploaded to dir (assumes only scan files are being received)
def scan_done_uploading(dir):
    if not os.path.exists(dir):
        return False

    num_files = len([f for f in os.listdir(
        dir) if os.path.isfile(os.path.join(dir, f))])
    if num_files == 0:
        return False
    json_file = os.path.join(dir, os.path.basename(dir) + '.json')
    if os.path.exists(json_file):
        with open(json_file) as f:
            data = json.load(f)
            expected_num = data.get('number_of_files', config.upload.number_of_files)
    else:
        return False
    return num_files == expected_num


# trigger indexing of scan
def trigger_indexing(basename, log):
    index_url = config.upload.index_url + basename
    log.info('Indexing ' + basename + ' at ' + index_url + ' ...')
    try:
        response = urlopen(index_url)
        html = response.read()
        log.info('Index ' + basename + ' successfully.')
    except URLError as e:
        log.warning('Error indexing ' + index_url + ': ' + str(e.reason))


# trigger video conversion of scan
def trigger_video_conversion(basename, log):
    convert_video_url = config.upload.convert_video_url + basename
    log.info('Converting video ' + basename + ' at ' + convert_video_url + ' ...')
    try:
        response = urlopen(convert_video_url)
        html = response.read()
        log.info('Convert video' + basename + ' successfully.')
    except URLError as e:
        log.warning('Error converting video ' + convert_video_url + ': ' + str(e.reason))


# scan uploaed do some basic stuff with it
def preprocess(basename, log):
    trigger_video_conversion(basename, log)
    trigger_indexing(basename, log)


# calls processor server on given scan basename
def trigger_processing(basename, actions, log):
    process_url = config.upload.process_trigger_url
    log.info('Calling scan process script for ' + basename + ' at ' + process_url + ' ...')
    try:
        response = urlopen(url=process_url, data=urlencode({'scanId': basename, 'overwrite': 0, 'actions': actions}).encode())
        html = response.read()
        log.info(config.upload.process_complete_status + ' ' + basename + ' successfully.')
    except URLError as e:
        log.warning('Error calling scan process for ' + process_url + ': ' + e.reason)


# Receives file from request (consuming input)
# Writes file to output if specifed (otherwise, discards it)
def receive_file(request, filename, output=None):
    content_length = request.environ.get('CONTENT_LENGTH', 0)
    # TODO DEBUG STARTS HERE
    if 'Content-Range' in request.headers:
        # extract starting byte from Content-Range header string
        range_str = request.headers['Content-Range']
        start_bytes = int(range_str.split(' ')[1].split('-')[0])
        log.exception('Receiving %s: PARTIAL FILE RECEIVED: %s',
                      filename, range_str)
    if not content_length:
        content_length = 0
    else:
        content_length = int(content_length)
    content_read = 0
    chunk_size = 4096 * 4
    stream = request.environ['wsgi.input']
    while True:
        if content_read % (chunk_size * 1000) == 0:
            log.info("Receiving %s: Uploaded count: %d, \t Percent: %.2f",
                     filename, content_read, 100 * float(content_read) / content_length)
        try:
            chunk = stream.read(chunk_size)
        except Exception as e:
            log.exception('Receiving %s: Exception: %s while reading input. Aborting...',
                          filename, str(e))
            raise util.Error(message='Unexpected error while receiving', status_code=500)
        if len(chunk) == 0:
            break
        content_read += len(chunk)
        if output is not None:
            output.write(chunk)

    log.info("Receiving %s: Uploaded count: %d, \t Percent: %.2f",
             filename, content_read, 100 * float(content_read) / content_length)
    if output is None:
        log.info('Discarding received file ' + filename)

    if content_read != content_length:
        log.error('Receiving %s: Expected length %d, received length %d. Aborting...',
                  filename, content_length, content_read)
        raise util.Error(message='Unexpected error while receiving', status_code=400)


# Temporarily accept both PUT and POST.
# TODO: Remove POST. PUT is more appropriate
@app.route('/upload', methods=['PUT', 'POST'])
def upload_file():
    try:
        filename = request.headers.get('FILE_NAME')
        if 'process' in request.args:
            auto_process_scan = request.args.get(
                'process').lower() in ['true', '1']
        else:
            auto_process_scan = len(config.upload.autoprocess) > 0
        log.info('Receiving %s, autoprocess=%s', filename, auto_process_scan)

        if allowed_file(filename):
            filename = secure_filename(filename)
            # determine final staging path for file and check if the file already exists
            basename = os.path.splitext(filename)[0].split('.')[0]
            stagingdir = os.path.join(config.upload.staging_dir, basename)
            stagingpath = os.path.join(stagingdir, filename)
            if os.path.exists(stagingpath):
                log.info('File already exists on server: %s', stagingpath)
                return util.ret_ok('File already exists on server')
            # temp location to receive stream
            tmppath = os.path.join(config.upload.tmp_dir, filename)
            with open(tmppath, 'wb') as f:
                receive_file(request, filename, f)

            return util.ret_ok()
        else:
            log.error('File type not allowed: ' + filename)
            log.error(request)
            raise util.Error(message=('File type not allowed: ' + filename), status_code=415)
    except Exception as e:
        log.error(traceback.format_exc())
        # raise util.Error(message=('Unknown exception encountered %s' % str(e)), status_code=500)
        raise e


@app.route('/received', methods=['GET'])
@app.route('/received/<path:filename>', methods=['GET'])
def get_file(filename=None):
    base_dir = config.upload.staging_dir
    path = base_dir
    if filename:
        full_path = os.path.join(path, filename)
        if not os.path.isdir(full_path):
            return send_from_directory(path, filename)
        else:
            path = full_path

    tmpl = '''
<!doctype html>
<title>Path: {{ tree.name }}</title>
<h1>{{ tree.name }}</h1>
<table cellpadding="10">
    <tr><th>Name</th><th>Last Modified</th><th>Size</th></tr>
{%- for item in tree.children recursive %}
    <tr>
      <td><a href="/{{ item.relative_name }}">{{ item.name }}</a></td>
      <td>{{ item.modifiedAt }}</td>
      <td>{{ item.fileSize }}</td>
    </tr>
{%- endfor %}
</table>
    '''
    return render_template_string(tmpl, tree=io.make_tree(base_dir, path))


@app.route('/verify', methods=['GET'])
def verify_file():
    filename = unquote(request.args.get('filename'))
    checksum = request.args.get('checksum')

    filename = secure_filename(filename)

    basename = os.path.splitext(filename)[0].split('.')[0]
    stagingdir = os.path.join(config.upload.staging_dir, basename)
    stagingpath = os.path.join(stagingdir, filename)
    tmppath = os.path.join(config.upload.tmp_dir, filename)

    if os.path.exists(stagingpath):
        log.info('File already exists on server: %s', stagingpath)
        return util.ret_ok('File already exists on server')

    if not os.path.exists(tmppath):
        log.error('File %s does not exist', tmppath)
        raise util.Error(message=('File %s does not exist' % tmppath), status_code=404)

    calculated_checksum = io.md5(tmppath)

    valid = calculated_checksum == checksum
    if valid:
        log.info('File %s successfully verified', filename)
        # move to staging area dir and return
        io.ensure_dir_exists(stagingdir)
        shutil.move(tmppath, stagingpath)
        if os.path.isfile(stagingpath):
            log.info('Staged ' + filename + ' to ' + stagingdir)
        else:
            log.error('Move ' + filename + ' to ' + stagingdir + 'failed!')
            raise util.Error(message=(f'Error in moving file from tmp to staging {stagingdir}'), 
                        status_code=400)

        # If uploading is complete try to trigger processing
        if scan_done_uploading(stagingdir):
            log.info('Scan done uploading to ' + stagingdir)
            indexThread = threading.Thread(target=preprocess, args=(basename, log))
            indexThread.start()
            if len(config.upload.autoprocess):
                process_scan(basename)
        return util.ret_ok()
    else:
        if os.path.isfile(tmppath):
            os.remove(tmppath)
        log.error('File %s: hash mismatch. Given: %s, calculated: %s',
                  filename,
                  checksum,
                  calculated_checksum)
        raise util.Error(message=('File hash mismatch. Given: %s, calculated: %s' % (checksum, calculated_checksum)),
                    status_code=400)


@app.route('/process/<scanid>', methods=['GET'])
def process_scan(scanid=None):
    process_list = OmegaConf.to_object(config.upload.autoprocess)
    if len(process_list) > 0:
        processThread = threading.Thread(
            target=trigger_processing,
            args=(scanid, json.dumps(process_list), log)
        )
        processThread.start()
    return util.ret_ok()


def get_app(*args, **kwargs):
    return app

@hydra.main(config_path="../config", config_name="config")
def main(cfg : DictConfig):
    port = int(os.environ.get("PORT", cfg.upload.port))
    workers = min(multiprocessing.cpu_count(), cfg.upload.workers)
    worker_class = cfg.upload.worker_class

    ini_file_path = os.path.join(get_original_cwd(), 'config/upload.ini')

    ini_parser = ConfigParser()
    ini_parser.read(ini_file_path)
    ini_parser.set('server:main', 'host', cfg.upload.host)
    ini_parser.set('server:main', 'port', str(port))
    ini_parser.set('server:main', 'workers', str(workers))
    ini_parser.set('server:main', 'worker_class', worker_class)

    output_ini_file_path = os.path.join(os.getcwd(), 'upload.ini')
    with open(output_ini_file_path, 'w') as f:
        ini_parser.write(f)

    global config
    config = cfg

    # hydra by default is on another directory
    io.call(['gunicorn', '--paste', output_ini_file_path], log, desc='Receive file uploads', rundir=get_original_cwd())

if __name__ == "__main__":
    main()
