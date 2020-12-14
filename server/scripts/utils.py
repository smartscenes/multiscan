import os
import sys
import shutil
import re


def print_m(msg):
    msg_color = '\033[0m'
    sys.stdout.write(f'{msg_color}{msg}{msg_color}\n')


def print_w(warning):
    warn_color = '\033[93m'
    msg_color = '\033[0m'
    sys.stdout.write(f'{warn_color}Warning: {warning} {msg_color}\n')


def print_e(error):
    err_color = '\033[91m'
    msg_color = '\033[0m'
    sys.stdout.write(f'{err_color}Error: {error} {msg_color}\n')


def file_exist(file_path, ext=''):
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return False
    elif ext in os.path.splitext(file_path)[1] or not ext:
        return True
    return False


def folder_exist(folder_path):
    if not os.path.exists(folder_path) or os.path.isfile(folder_path):
        return False
    else:
        return True


def make_clean_folder(path_folder):
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)
    else:
        shutil.rmtree(path_folder)
        os.makedirs(path_folder)


def sorted_alphanum(file_list):
    """sort the file list by arrange the numbers in filenames in increasing order

    :param file_list: a file list
    :return: sorted file list
    """
    if len(file_list) <= 1:
        return file_list
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(file_list, key=alphanum_key)


def get_file_list(path, ext=''):
    if not os.path.exists(path):
        raise OSError('Path {} not exist!'.format(path))

    file_list = []
    for filename in os.listdir(path):
        file_ext = os.path.splitext(filename)[1]
        if (ext in file_ext or not ext) and os.path.isfile(os.path.join(path, filename)):
            file_list.append(os.path.join(path, filename))
    file_list = sorted_alphanum(file_list)
    return file_list