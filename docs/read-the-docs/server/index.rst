Processing Server
=================
The processing server has 3 main functionalities:

1. Stage uploaded scans by the devices (iOS or Android) and trigger scan processing. To ensure that scans can be automatically processed, the scans should be placed in a directory with lots of space and accessible to the scanning processor.
2. Process staged scans. Handle reconstruction processing request from Web-UI, when user press interactive buttons on Web-UI.
3. Index staged scans. Go through scan folders and collate information about the scans.

Installation
------------

Requirements
~~~~~~~~~~~~
+--------------------------------------------------------------------------+
| Suggested requirements                                                   |
+===================+======================================================+
| Operating systems | Linux (Ubuntu 18.04 / 20.04)                         |
+-------------------+------------------------------------------------------+
| CPU               | Recent Intel or AMD cpus                             |
+-------------------+------------------------------------------------------+
| RAM               | 32 GB                                                |
+-------------------+------------------------------------------------------+
| GPU               | NVIDIA GPU with CUDA 10.1+                           |
+-------------------+------------------------------------------------------+
| CMake             | version 3.19+                                        |
+-------------------+------------------------------------------------------+


Linux
~~~~~

1. Clone MultiScan
``````````````````
.. code-block:: bash

    git clone git@github.com:3dlg-hcvc/multiscan.git
    cd multiscan

2. Setup Python Environments
````````````````````````````
We use Conda environment here, which makes install c/c++ and python libraries dependencies easy. We use Python 3.x in MultiScan.

.. code-block:: bash

    conda create -n multiscan python=3.6
    conda activate multiscan
    conda install -c conda-forge libpng libtiff libjpeg-turbo
    conda install -c conda-forge tbb-devel=2020.2.0
    conda install -c conda-forge mesalib libglu

1. CMake Build & Install
````````````````````````
.. code-block:: bash

    mkdir build && cd build
    cmake -DCMAKE_PREFIX_PATH="${CONDA_PREFIX}" \
          -DCMAKE_INCLUDE_PATH="${CONDA_PREFIX}/include" \
          -DCMAKE_LIBRARY_PATH="${CONDA_PREFIX}/lib" \
          -DCMAKE_INSTALL_PREFIX="${CONDA_PREFIX}" \
          ..
    make -j$(nproc)
    make install
    cd ..

Environment variables: ``CONDA_PREFIX``: The path to the activated conda environment, for example `$HOME/anaconda3/envs/multiscan`. ``nproc``: The number of processing units available in the current system. The header files and the libraries will be installed in the conda environment at ``CONDA_PREFIX`` path.

1. Python Libraries Install
```````````````````````````
.. code-block:: bash

    pip install -e .

Python libraries installation verification:

.. code-block:: bash

    python -c "import multiscan"

.. todo:: 

    MacOS installation


Configurations
--------------

Configurable parameters are listed in config.yaml. Parameters can be overridden by command line as `config_parameter`=`new value`, for example:

.. code-block:: bash

    python upload.py upload.workers=8 upload.port=8080

This command line changes the default upload server cpu workers from 4(default) to 8, and the upload server port number from 8000 to 8080.

This command line override syntax also applies to the processing server:

.. code-block:: bash

    python process.py staging_dir=/path/to/staging_folder process.port=6000

We use `hydra`_ for the  hierarchical configuration, `hydra` also allows dynamic command line tab completion, you can enable tab completion via:

.. code-block:: bash

    eval "$(python python_script.py -sc install=bash)"

Configuration files:
    | `config.yaml` - Main configuration file
    | `multiscan.json` - Metadata for MultiScan assets for use with the Scene Toolkit viewer
    | `config/scan_stages.json` - The stages of the scan pipeline (so we can track progress)
    | `config/upload.ini` - Configuration file for upload server

Upload
------

The upload script receives scan files (`.mp4`, `.depth.zlib`, `.confidence.zlib`, `.json`, `.jsonl`) from the devices with Scanner App installed and stages them in a staging folder for scan processing. These files first placed in the `tmp` directory before being moved into the `staging` directory after verification. Uses `flask`_ with `gunicorn`_ with specified number of worker threads on port 8000 by default.

Start uploading server by:

.. code-block:: bash

    python upload.py **configuration override** # Start the upload server, recieve files from scanner app

Process
-------

Start process server on port 5000 by:

.. code-block:: bash

    python process.py **configuration override** # Start the process server, recieve process request from web-ui

The server is a simple flask server that only handles one request at a time (will block until scan is processed).

The scan processing can be broken down into the following components:

Compressed Streams Decoding
~~~~~~~~~~~~~~~~~~~~~~~~~~~
The first step is decoding RGB and depth frames from the uploaded compressed streams.
Color RGB frames are extracted by `ffmpeg`, which is used for texturing the reconstructed mesh.
Depth frames are extracted by zlib, implementation details in `scripts/depth_decode.py`. The depth maps are used for the mesh reconstruction.

We filter the recorded depth maps before reconstruction. Depth maps from mobile devices tend to be low resolution and noisy. The raw acquired depth maps contain noises and outliers, especially in the boundaries with big depth difference, which will introduce artifacts in the reconstruction results. To ensure that we only consider high-quality depth values, we filter the depth values by confidence values. In addition, we filter out pixels where the depth values change more than 5 cm between adjacent frames.

Reconstruction
~~~~~~~~~~~~~~
We use the open source library `Open3D`_ for the 3D reconstruction. The input depth frames with given camera intrinsics and extrinsics are integrated into a Truncated Signed Distance Function (TSDF) volume (`Curless1996`_). The mesh is extracted from the TSDF volume with marching cubes algorithm (`LorensenAndCline1987`_). The reconstruction is accelerated with CUDA enabled NVIDIA GPU. We didn’t add RGB frames when reconstruction as it will add additional computation complexity and time. Open3D also comes with more advanced reconstruction algorithms, e.g VoxelHashing, Simultaneous Localization and Calibration (SLAC). Same for the purpose of efficiency and time, we didn’t use these advanced algorithms, and leave this long standing reconstruction task as future improvements. The current TSDF integration algorithm takes XXX time for integrating XXX depth frames.
Depth preprocessing We filter the recorded depth maps. Depth maps from mobile devices tend to be low resolution and noisy. The raw acquired depth maps contain noises and outliers, especially in the boundaries with big depth difference, which will introduce artifacts in the reconstruction results. To ensure that we only consider high-quality depth values, we filter the depth values by confidence values. In addition, we filter out pixels where the depth values change more than 5 cm between adjacent frames.

Texturing
~~~~~~~~~
We use MVS-Texturing (`Waechter2014`_) a texturing frame-work for large-scale 3D reconstruction. Instead of using every collected RGB frame, we choose to use 1/10 frames in the acquired RGB stream, with the joint consideration of texturing quality and processing time.

Segmentation
~~~~~~~~~~~~
Before crowdsourcing semantic annotation, we apply hierarchical graph-based 3D triangles segmentation algorithms adopted from ScanNet to get over segmented triangle clusters as references for the semantic annotation. This segmentation algorithm treats the triangle mesh as a connected graph, where the nodes in the graph are the mesh vertices connected by the mesh edges. The segmentation algorithm outputs 2 levels (coarse, fine) of the segmentation results. The coarse result takes only the geometric information vertex normals to compute the weights for the graph, and applies the graph cut algorithm to get the segmentations. The finer results jointly consider the RGB color and vertex normals and break the clusters in the coarse segmentation result into more and finer clusters. The finer segmentation helps to segment out objects and parts with similar geometry but have different visual appearances. We apply 3 different parameter settings to get more levels of the unsupervised segmentation results.

Rendering
~~~~~~~~~
This step creates the rendered PNG format images of the reconstructed and textured mesh, and the unsupervised segmentation results with each segment assigned with a random color. `scripts/render.py` utilize Open3D triangle mesh visualization with headless rendering, to render the ply meshes, and utilize Pyrender with EGL GPU-accelerated rendering to render textured obj meshes.

.. todo::

    Use one framework for the rendering, use Pyrender.

Indexing
--------
Indexing is used to collate information about the scans and index them, and has 3 main functionalities:
1. Creates index of scans in the staged directory and outputs a csv file with metadata of each scan.
2. Index both staged and checked scans and updates Web-UI database.
3. Web service entry point for monitoring and triggering of indexing of scans.

Start indexing server by:

.. code-block:: bash

    python monitor.py  # Web service entry point for monitoring and triggering of indexing of scans.

Scripts that are used for the indexing:
    | `monitor.py` - Web service entry point for monitoring and triggering of indexing of scans. Run following command to start the monitor server on port 5001 (simple flask server).
    | `index.py` - Creates index of scans in a directory and outputs a csv file
    | `scripts/index_multiscan.sh` - Index both staging and checked scans and updates WebUI db


.. _hydra: https://hydra.cc/docs/1.2/intro/
.. _Open3D: https://github.com/intel-isl/Open3D
.. _Curless1996: https://graphics.stanford.edu/papers/volrange/volrange.pdf
.. _LorensenAndCline1987: https://dl.acm.org/doi/10.1145/37402.37422
.. _Waechter2014: https://www.semanticscholar.org/paper/Let-There-Be-Color!-Large-Scale-Texturing-of-3D-Waechter-Moehrle/b8f1ea118487d8500d45e5fbf95ab80eedd7fa92
.. _flask: http://flask.pocoo.org/
.. _gunicorn: http://gunicorn.org/



