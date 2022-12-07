#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name="multiscan",
    version="1.0",
    author="3dlg-hcvc",
    url="https://github.com/3dlg-hcvc/multiscan.git",
    description="Code for MultiScan",
    packages=find_packages(exclude=("configs", "tests")),

    include_package_data=True,
    install_requires=["configparser==5.0.2", "decord==0.6.0", "Flask==1.1.2", "gevent==21.1.2", "MarkupSafe==2.0.1",
                      "gunicorn==19.9.0", "hydra-core==1.2.0", "imageio==2.9.0", "matplotlib==3.3.4", "numpy==1.19.5",
                      "opencv-python==4.5.1.48", "pandas==1.4.3", "Paste==3.5.0", "PasteDeploy==2.1.1", "Pillow==8.2.0", "psutil==5.9.3",
                      "progress==1.6", "protobuf==3.13.0", "pymeshlab==0.2.1", "pyrender==0.1.45", "pytimeparse==1.1.8", 
                      "pyglet==1.5.20", "plyfile==0.7.4", "scipy==1.5.4", "requests==2.22.0", "tqdm==4.64.0", "trimesh==3.9.16"]
)

