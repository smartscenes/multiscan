# Multiscan Staging Server

The staging server is broken down into the following components:

1. Stage uploaded scans by the devices with scanner app installed and trigger scan processing. To ensure that scans can be
   automatically processed, the scans should be placed in a directory with sufficient free space and accessible to the scanning
   processor.
2. Process staged scans. Handle reconstruction processing request from Web-UI, when user press interactive buttons on
   Web-UI.
3. Index staged scans. Go through scan folders and collate information about the scans.

## Dependencies

Server requires installing prerequisites to perform scan processing. Please follow the installation instruction [**here**](../docs/INSTALL.md).

## Configuration
Configurable parameters are listed in [config.yaml](../config/config.yaml). Parameters can be overriden by command line as follows:
```bash
python upload.py upload.workers=4 upload.port=8080
```
```bash
python process.py reconstruction.frames.step=2 thumbnail.thumbnail_ext=_thumb.png
```

`hydra` also allows dynamic command line tab completion, you can enable tab completion via:
```
eval "$(python python_script.py -sc install=bash)" 
```
You can find more details about `hydra` [**here**](https://hydra.cc/docs/intro/)

Configuration files:
- `config.yaml` - Main configuration file
- `multiscan.json` - Metadata for MultiScan assets for use with the Scene Toolkit viewer
- `config/scan_stages.json` - The stages of the scan pipeline (so we can track progress)
- `config/upload.ini` - Configuration file for upload server

| :zap:  Note the working directory need to be in `multiscan/server`|
|-------------------------------------------------------------------|

## Staging Directory Setup

Since staging folder will store a great amount of uploaded scans, and is required to have a large number of storage
space. Usually, the staging folder is in a different directory to the server code directory, thus you can create
symbolic links to the `staging` directory.

``` bash
ln -s "$(realpath /path/to/staging folder)" staging
```

## Upload Server

The upload script receives scan files (`.mp4`, `.depth.zlib`, `.confidence.zlib`, `.json`, `.jsonl`) from the devices
with Scanner App installed and stages them in a staging folder for scan processing. These files first placed in
the `tmp` directory before being moved into the `staging` directory after verification. Uses [flask](http://flask.pocoo.org/)
with [gunicorn](http://gunicorn.org/) with specified number of worker threads on port 8000 by default.   
Start uploading server by:
```bash
python upload.py **configuration override** # Start the upload server, recieve files from scanner app
```

## Scan Processing Server
Start process server on port 5000 by:
```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(realpath ../install/lib)
python process.py **configuration override** # Start the process server, recieve process request from web-ui
```
The server is a simple flask server that only handles one request at a time (will block until scan is processed).

The scan processing can be broken down into the following components:

1. ### Decode RGB and depth frames from compressed streams
   The `convert` checkbox in Web-UI is used to control whether extract rgb and depth frames from the uploaded compressed
   scan streams
    - Color RGB frames are extracted by `ffmpeg`.
    - Depth frames are extracted by `zlib`, implementation details in `scripts/depth_decode.py`.

2. ### Scan Reconstruction
   **Open3D RGB-D Reconstruction Pipeline**

   When the depth sensor is available, the RGB-D data can be acquired, Open3D RGB-D reconstruction pipeline can provide
   more robust reconstruction result.

   **Meshroom RGB Photogrammetric Reconstruction Pipeline**

   When only RGB data is available, Meshroom photogrammetric pipeline based on structure from motion(sfm) and multi-view
   stereo(mvs) reconstruction pipeline can be used.

3. ### Mesh Topology Cleanup and Decimation
   Meshes extracted by Open3D RGB-D reconstruction pipeline usually contains millions of vertices and faces, we
   use [Instant Meshes](https://github.com/wjakob/instant-meshes.git) to perfrom mesh topology decimation
   after reconstruction to reduce mesh complexity, and keep geometry unchanged as much as possible. We also use [PyMeshLab](https://pypi.org/project/pymeshlab/) for mesh cleanup.

   Meshroom reconstruction pipeline has built in mesh cleanup functionality, we don't need to apply topology cleanup and
   decimation use Instant Meshes if user choose to use this pipeline.

4. ### Texturing
   To improve the visual appearance of our reconstructed mesh from Open3D pipeline, the decimated mesh will be textured. There are two options for texturing the reconstructed mesh: 1. [mvs-texturing](https://github.com/3dlg-hcvc/mvs-texturing.git) 2. [Meshroom Texturing Node](https://github.com/alicevision/meshroom). By default we use mvs-texturing, it is much faster than meshroom texturing and has less banding artifacts.

5. ### Segmentation
   Based on the segmentator in ScanNet, we extend the algorithm to take advantage of both vertex colors and vertex normals, and implemented a two-stage hierarchical segmentator. The first stage segments the mesh with weight from vertex normals. Then for each segmented cluster, the vertex colors are added to the weights to perform another segmentation step.

6. ### Rendering
    - `scripts/render.py` utilize Open3D triangle mesh visualization with headless rendering, to render reconstruted ply meshes, and utilize Pyrender with EGL GPU-accelerated rendering to render textured obj meshes.

- `scan_processor.py` - Main scan processing script which let you process scans without interaction without WebUI. You can specify which steps to process as follows:
```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$(realpath ../install/lib)
python scan_processor.py process.input_path=path/to/staging/scanID process.actions='[recons, convert, texturing ...(other steps)]'
```

## Indexing Server

Indexing scripts are used to collate information about the scans and index them.
```
python monitor.py  # Web service entry point for monitoring and triggering of indexing of scans.
```

- `monitor.py` - Web service entry point for monitoring and triggering of indexing of scans. Run following command to start the monitor server on port 5001 (simple flask server).
- `index.py` - Creates index of scans in a directory and outputs a csv file
- `scripts/index_multiscan.sh` - Index both staging and checked scans and updates WebUI db

## Statistics computation scripts

- `compute_annotation_stats.py` - Compute aggregated annotation statistics
- `compute_timings.py` - Compute processing times for scans
- `scripts/combine_stats.py` - Combines statistics with index
