#!/usr/bin/env python
#
# Recommended:
# Install virtualenv
# Create virtualenv
# pip install flask
# Run with ./monitor.py (or python monitor.py on Windows)

import json
import logging
import os
from threading import Lock

import requests
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

import hydra
from hydra.utils import get_original_cwd
from omegaconf import DictConfig, OmegaConf

import index
from multiscan.utils import io

config = OmegaConf.load(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../config/config.yaml'))

# for locking indexing resources
INDEX_LOCK = Lock()

# for locking convert video lock
CONVERT_VIDEO_LOCK = Lock()

app = Flask(__name__)

FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger('monitor')
log.setLevel(logging.INFO)


def post(url, data, log):
    log.info('Connecting to ' + url + ' ...')
    try:
        resp = requests.post(url, json=data)
        log.info('Connected to ' + url + ' successfully.')
        return {'status': 'ok', 'response': resp.text}
    except requests.exceptions.RequestException as e:
        log.warning('Error connecting to ' + url + ': ' + e.reason)
        return {'status': 'error', 'message': e.reason}


@app.before_request
def log_request():
    log.info('Got request: %s', request.path)


# Indexes scan
@app.route('/index/<dirname>')
def index_scan(dirname):
    dirname = secure_filename(dirname)
    path = os.path.join(app.config['STAGING_FOLDER'], dirname)

    # Indexing
    with INDEX_LOCK:
        indexfile = os.path.join(app.config['STAGING_FOLDER'], app.config['indexfile'])
        indexed = index.index({
            'input': path, 'output': indexfile, 'root': app.config['STAGING_FOLDER'],
            'single': True, 'append': True, 'checkCleaned': True,
            'source': app.config['source'], 'datasets': app.config['datasets'],
            'stages': app.config['stages'],
            'includeAll': True
        })
        if indexed:
            res = post(config.index.populate_single_url, list(indexed.values()), log)
            if res.get('status') == 'ok':
                return res.get('response')
            else:
                resp = jsonify({"message": res.message})
                resp.status_code = 500
                return resp
        else:
            return 'Nothing to index'


@app.route('/index')
def index_all():
    with INDEX_LOCK:
        ret = io.call([config.index.index_all_bin, 
                       '--staging_dir', config.index.staging_dir,
                       '--populate_url', config.index.populate_url,
                       '--csv', os.path.join(config.index.staging_dir, config.index.csv_file),
                       '--json', os.path.join(config.index.staging_dir, config.index.json_file)],
                       log, desc='index all scans')
        if ret < 0:
            resp = jsonify({"message": 'Error indexing all scans'})
            resp.status_code = 500
            return resp
        else:
            return 'done'


# Converts the mp4 to preview mp4 and thumbnails
@app.route('/convert-video/<dirname>')
def convert_video(dirname):
    dirname = secure_filename(dirname)
    path = os.path.join(app.config['STAGING_FOLDER'], dirname)

    # Convert
    with CONVERT_VIDEO_LOCK:
        ret2 = io.call([config.process.thumbnail.mp42thumbnail_bin, '--skip-done', 
                        path, str(config.process.thumbnail.thumbnail_width)],
                        log, desc='mp4-to-thumbnail')
        ret1 = io.call([config.process.thumbnail.mp42preview_bin, '--skip-done', 
                        path, str(config.process.thumbnail.preview_width)],
                        log, desc='mp4-to-preview')
        if ret1 < 0 or ret2 < 0:
            resp = jsonify({"message": 'Error converting mp4 to preview/thumbnail'})
            resp.status_code = 500
            return resp
        else:
            return 'done'


@app.route('/health')
def health():
    return 'ok'

@hydra.main(config_path="../config", config_name="config")
def main(cfg : DictConfig):
    if not os.path.isabs(cfg.index.index_all_bin):
        cfg.index.index_all_bin = os.path.join(get_original_cwd(), cfg.index.index_all_bin)
    if not os.path.isabs(cfg.process.thumbnail.mp42preview_bin):
        cfg.process.thumbnail.mp42preview_bin = os.path.join(get_original_cwd(), cfg.process.thumbnail.mp42preview_bin)
    if not os.path.isabs(cfg.process.thumbnail.mp42thumbnail_bin):
        cfg.process.thumbnail.mp42thumbnail_bin = os.path.join(get_original_cwd(), cfg.process.thumbnail.mp42thumbnail_bin)
    if not os.path.isabs(cfg.index.staging_dir):
        cfg.index.staging_dir = os.path.join(get_original_cwd(), cfg.index.staging_dir)
    if not os.path.isabs(cfg.index.stages_file):
        cfg.index.stages_file = os.path.join(get_original_cwd(), cfg.index.stages_file)


    app.config['STAGING_FOLDER'] = cfg.index.staging_dir
    app.config['indexfile'] = cfg.index.csv_file
    app.config['source'] = cfg.index.source
    app.config['datasets'] = cfg.index.datasets

    if os.path.isfile(cfg.index.stages_file):
        with open(cfg.index.stages_file) as json_data:
            app.config['stages'] = json.load(json_data)

    global config
    config = cfg

    # hydra by default is on another directory
    cwd = os.getcwd()
    os.chdir(get_original_cwd())
    app.run(host=cfg.index.host, port=cfg.index.port, debug=cfg.debug)
    os.chdir(cwd)


if __name__ == "__main__":
    main()
