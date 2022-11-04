import datetime
import json
import hashlib
import os
import re
import shutil
import subprocess as subp
import sys
import traceback
import psutil
import resource
import multiprocessing
import multiprocessing.pool

from timeit import default_timer as timer
from enum import Enum

def file_exist(file_path, ext=''):
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return False
    elif ext in os.path.splitext(file_path)[1] or not ext:
        return True
    return False


def is_non_zero_file(file_path):
    return True if os.path.isfile(file_path) and os.path.getsize(file_path) > 0 else False


def file_extension(file_path):
    return os.path.splitext(file_path)[1]


def folder_exist(folder_path):
    if not os.path.exists(folder_path) or os.path.isfile(folder_path):
        return False
    else:
        return True


def ensure_dir_exists(path):
    try:
        if not os.path.isdir(path):
            os.makedirs(path)
    except OSError:
        raise


def make_clean_folder(path_folder):
    try:
        if not os.path.exists(path_folder):
            os.makedirs(path_folder)
        else:
            shutil.rmtree(path_folder)
            os.makedirs(path_folder)
    except OSError:
        if not os.path.isdir(path_folder):
            raise


def sorted_alphanum(file_list):
    """sort the file list by arrange the numbers in filenames in increasing order

    :param file_list: a file list
    :return: sorted file list
    """
    if len(file_list) <= 1:
        return file_list, [0]

    def convert(text): return int(text) if text.isdigit() else text

    def alphanum_key(key): return [convert(c)
                                   for c in re.split('([0-9]+)', key)]

    indices = [i[0]
               for i in sorted(enumerate(file_list), key=lambda x: alphanum_key(x[1]))]
    return sorted(file_list, key=alphanum_key), indices

def get_file_list(path, ext='', join_path=True):
    file_list = []
    if not os.path.exists(path):
        return file_list

    for filename in os.listdir(path):
        file_ext = file_extension(filename)
        if (ext in file_ext or not ext) and os.path.isfile(os.path.join(path, filename)):
            if join_path:
                file_list.append(os.path.join(path, filename))
            else:
                file_list.append(filename)
    file_list, _ = sorted_alphanum(file_list)
    return file_list

def get_folder_list(path, join_path=True):
    if not os.path.exists(path):
        raise OSError('Path {} not exist!'.format(path))

    folder_list = []
    for foldername in os.listdir(path):
        if not os.path.isdir(os.path.join(path, foldername)):
            continue
        if join_path:
            folder_list.append(os.path.join(path, foldername))
        else:
            folder_list.append(foldername)
    folder_list, _ = sorted_alphanum(folder_list)
    return folder_list


def filesize(file_path):
    if os.path.isfile(file_path):
        return os.path.getsize(file_path)
    else:
        return 0


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


def write_json(data, filename, indent=2):
    if folder_exist(os.path.dirname(filename)):
        with open(filename, "w+") as fp:
            json.dump(data, fp, indent=indent)
    if not file_exist(filename):
        raise OSError('Cannot create file {}!'.format(filename))


def read_json(filename):
    if file_exist(filename):
        with open(filename, "r") as fp:
            data = json.load(fp)
        return data

def limit_memory(maxsize):
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    # print(f'memory limit {soft} TO {hard}')
    # print(f'memory limit set to {maxsize} GB')
    resource.setrlimit(resource.RLIMIT_AS, (maxsize, hard))

# TODO: make memory limitation configurable
def call(cmd, log, rundir='', env=None, desc=None, cpu_num=0, mem=48, print_at_run=True, test_mode=False):
    if not cmd:
        log.warning('No command given')
        return 0
    if test_mode:
        log.info('Running ' + str(cmd))
        return -1
    cwd = os.getcwd()
    res = -1
    prog = None

    # constraint cpu usage with taskset
    if cpu_num > 0:
        all_cpus = list(range( min(psutil.cpu_count(), cpu_num)))
        sub_cpus = all_cpus[:cpu_num]
        str_cpus = ','.join(str(e) for e in sub_cpus)
        taskset_cmd = ['taskset', '-c', str_cpus]
        cmd = taskset_cmd + cmd
    
    try:
        start_time = timer()
        if rundir:
            os.chdir(rundir)
            log.info('Currently in ' + os.getcwd())
        log.info('Running ' + str(cmd))
        log.info(f'memory limit set to {mem} GB')
        setlimits = lambda: limit_memory(mem*1000*1000*1000) # in GB
        prog = subp.Popen(cmd, stdout=subp.PIPE, stderr=subp.STDOUT, env=env, preexec_fn=setlimits)
        # print output during the running
        if print_at_run:
            while True:
                nextline = prog.stdout.readline()
                if nextline == b'' and prog.poll() is not None:
                    break
                sys.stdout.write(nextline.decode("utf-8"))
                sys.stdout.flush()
        
        out, err = prog.communicate()
        if out:
            log.info(out.decode("utf-8"))
        if err:
            log.error('Errors reported running ' + str(cmd))
            log.error(err.decode("utf-8"))
        end_time = timer()
        delta_time = end_time - start_time
        desc_str = desc + ', ' if desc else ''
        desc_str = desc_str + 'cmd="' + str(cmd) + '"'
        log.info('Time=' + str(datetime.timedelta(seconds=delta_time)) + ' for ' + desc_str)
        res = prog.returncode
    except KeyboardInterrupt:
        log.warning("Keyboard interrupt")
    except Exception as e:
        if prog is not None:
            prog.kill()
            out, err = prog.communicate()
        log.error(traceback.format_exc())
    os.chdir(cwd)
    return res

# https://stackoverflow.com/questions/3431825/generating-a-md5-checksum-of-a-file
def md5(filename, blocksize=65536):
    hash = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(blocksize), b''):
            hash.update(chunk)
    return hash.hexdigest()

# http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size
def natural_size(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


class TIMEOUT(Enum):
    SECOND = 1
    MINUTE = 60
    HOUR = 3600

# reference https://stackoverflow.com/questions/6974695/python-process-pool-non-daemonic
class NoDaemonProcess(multiprocessing.Process):
    # make 'daemon' attribute always return False
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass

class NoDaemonPool(multiprocessing.pool.Pool):
    _wrap_exception = True

    def Process(self, *args, **kwds):
        proc = super(NoDaemonPool, self).Process(*args, **kwds)
        proc.__class__ = NoDaemonProcess
        return proc
        

# set mem limit for program
# reference https://stackoverflow.com/questions/41105733/limit-ram-usage-to-python-program
def set_memory_limit(percentage: float):
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (get_memory() * 1024 * percentage, hard))

def get_memory():
    with open('/proc/meminfo', 'r') as mem:
        free_memory = 0
        for i in mem:
            sline = i.split()
            if str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                free_memory += int(sline[1])
    return free_memory

def memory_limit(percentage=0.8):
    def decorator(function):
        def wrapper(*args, **kwargs):
            set_memory_limit(percentage)
            try:
                return function(*args, **kwargs)
            except MemoryError:
                mem = get_memory() / 1024 /1024
                sys.stderr.write('\n\nERROR: Memory Exception, remaining memory  %.2f GB\n' % mem)
                sys.exit(1)
        return wrapper
    return decorator
