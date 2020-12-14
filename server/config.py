import os
import util

# Server configuration
DATA_SERVER = 'http://localhost:3030'
TEMP_FOLDER = 'tmp'
STAGING_FOLDER = 'staging'
AUTOPROCESS = True

# General paths to binaries
SCRIPT_DIR = util.getScriptPath()
SOURCE_DIR = os.path.join(SCRIPT_DIR, '..')

DATA_DIR = 'staging/'
COLOR_FOLDER = 'color'
DEPTH_FOLDER = 'depth'
RECONS_RESULT_DIR = ''
PHOTOGRAMMETRY_RESULT_DIR = ''


# System specific paths for processing server binaries
TOOLS_DIR = '../'
DECODE_DIR = 'scripts'
RECONS_DIR = 'reconstruction'
PHOTOGRAMMETRY_DIR = 'meshroom'

# where scan data is stored under as subdirs with unique ids
# STAGING_FOLDER_LOCAL = os.path.join(DATA_DIR, 'scans', 'staging')
