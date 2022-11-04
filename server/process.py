#!/usr/bin/env python
#
# Recommended:
# Install virtualenv
# Create virtualenv
# pip install flask
# Run with ./process.py (or python process.py on Windows)

import logging
import os
import psutil
from threading import Lock
from urllib.error import URLError
from urllib.request import urlopen

from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

import hydra
from hydra.utils import get_original_cwd
from omegaconf import DictConfig, OmegaConf

import scan_processor as sp
import util
from util import ProcessStage

config = OmegaConf.load(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../config/config.yaml'))

# for locking GPU resources
GPU_LOCK = Lock()

app = Flask(__name__)

FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger('processor')
log.setLevel(logging.INFO)


def trigger_indexing(basename, log):
    index_url = config.process.index_url + basename
    log.info('Indexing ' + basename + ' at ' + index_url + ' ...')
    try:
        response = urlopen(index_url)
        html = response.read()
        log.info('Index ' + basename + ' successfully.')
    except URLError as e:
        log.warning('Error indexing ' + index_url + ': ' + e.reason)


@app.route('/process/<dirname>')
def process_scan_dir(dirname):
    dirname = secure_filename(dirname)
    path = os.path.join(config.process.staging_dir, dirname)
    args = request.args
    if 'from' not in args and 'actions' not in args:
        proc_dict = {'all': True}
    else:
        proc_dict = {'from': args.get('from'), 'actions': args.get('actions')}
    proc_dict['overwrite'] = args.get('overwrite').lower() in [
        'true', '1', 'yes'] if 'overwrite' in args else False
    
    proc_dict = sp.update_config(proc_dict, OmegaConf.to_object(config.process.process_list))
    proc_cfg = OmegaConf.create(proc_dict)
    # allow add new keys
    OmegaConf.set_struct(config, False)
    proc_cfg = OmegaConf.merge(config, proc_cfg)

    if proc_cfg.get('overwrite'):
        # Check timestamp of request (only trigger if the last update timestamp before overwrite)
        # Prevents duplicates request
        timestamp = args.get('timestamp')
        if timestamp is None:
            resp = jsonify(
                {'message': 'Please provide timestamp with request'})
            resp.status_code = 400
            return resp
        # Request timestamp should be in milliseconds UTC
        timestamp = int(timestamp)
        newer = util.check_last_modified_newer(path, timestamp)
        if newer:
            resp = jsonify({'message': 'Scan ' + dirname +
                           ' modified after request issued, please resubmit request'})
            resp.status_code = 400
            return resp

    with GPU_LOCK:
        processed1 = sp.process_scan_dir(path, dirname, proc_cfg, ProcessStage.PRELIMINARY)

    trigger_indexing(dirname, log)

    with GPU_LOCK:
        processed2 = sp.process_scan_dir(path, dirname, proc_cfg, ProcessStage.EXTRA)

    trigger_indexing(dirname, log)

    return processed1 + "\n" + processed2

@hydra.main(config_path="../config", config_name="config")
def main(cfg : DictConfig):
    if not os.path.isabs(cfg.process.staging_dir):
        cfg.process.staging_dir = os.path.join(get_original_cwd(), cfg.process.staging_dir)

    # hydra by default is on another directory
    cwd = os.getcwd()
    OmegaConf.set_struct(cfg, False)
    cfg.dump_cfg_path = cwd
    global config
    config = cfg
    os.chdir(get_original_cwd())
    app.run(host=cfg.process.host, port=cfg.process.port, debug=cfg.debug)
    os.chdir(cwd)


if __name__ == "__main__":
    main()
