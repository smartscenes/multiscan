# Multiscan Staging Server

The staging server is broken down into the following components:

1. Stage uploaded scans by the devices (iPhone or iPad) and trigger scan processing. To ensure that scans can be automatically processed, the scans should be placed in a directory with lots of space and accessible to the scanning processor.
2. Process staged scans. Handle reconstruction processing request from Web-UI, when user press interactive buttons on Web-UI.
3. Index staged scans. Go through scan folders and collate information about the scans.

## Upload scripts

The upload script receives scan files (`.mp4`, `.depth.zlib`, `.confidence.zlib`, `.json`, `.jsonl`) from the devices with Scanner App installed and stages them in a staging folder for scan processing. These files first placed in the `tmp` directory before being moved into the `staging` directory.  Uses [flask](http://flask.pocoo.org/) with [gunicorn](http://gunicorn.org/) with 2 worker threads on port 8000.

- `install_deps.sh` - Run this to install python dependencies required for the upload server
- `start_upload_server.sh` - Run this to start the upload server. The main entry point is at `upload.py` (started automatically by this `.sh` script)
- `wsgi.py` - Web service wrapper for `upload.py`

### Staging Directory Setup
Since staging folder will store a great amount of uploaded scans, and is required to have a large number of storage space. Usually, the staging folder is in a different directory to the server code directory, thus you can create symbolic links to the `staging` directory.
``` bash
ln -s "$(realpath /path/to/staging folder)" staging
```

## Scan processing scripts

The scan processing can be broken down into the following components:

1. ### Decode RGB and depth frames from compressed streams
    The `convert` checkbox in Web-UI is used to control whether extract rgb and depth frames from the uploaded compressed scan streams
    - Color RGB frames are extracted by `ffmpeg`.
    - Depth frames are extracted by `zlib`, implementation details on `scripts.depth2png.py`.  

2. ### Scan Reconstruction
    **Open3D RGB-D Reconstruction Pipeline**

    When the depth sensor is available, the RGB-D data can be acquired, Open3D RGB-D reconstruction pipeline can provide more robust reconstruction result.

    **Meshroom RGB Photogrammetric Reconstruction Pipeline**

    When only RGB data is available, Meshroom photogrammetric pipeline based on structure from motion(sfm) and multi-view stereo(mvs) reconstruction pipeline can be used.

3. ### Mesh Topology Cleanup and Decimation
    Meshes extracted by Open3D RGB-D reconstruction pipeline usually contains millions of vertices and faces, we use [Instant Meshes](https://github.com/wjakob/instant-meshes.git) to perfrom mesh topology cleanup and decimation after reconstruction to reduce mesh complexity, and keep geometry unchanged as much as possible.

    Meshroom reconstruction pipeline has built in mesh cleanup functionality, we don't need to apply topology cleanup and decimation use Instant Meshes if user choose to use this pipeline.

4. ### Texturing
    After mesh topology cleanup and decimation, the color of vertices will no longer be preserved. In order to have a textured mesh we apply texturing process to map textures to the triangle meshes.

    We are working on utilize Meshroom pipeline's `Texturing` node to perform the texturing. Which requires a `.abc` format dense point cloud with camera poses stored in it, rgb color images for each camera view in the .abc file and the mesh as inputs.

5. ### Segmentation
    [Segmentor](https://github.com/ScanNet/ScanNet/tree/master/Segmentator) uses Felzenswalb and Huttenlocher's Graph Based Image Segmentation algorithm on computed mesh normals. It takes the cleaned and decimated triagnle mesh as input and output a `.segs.json` file, which contains segment indices for vertices in the mesh.

6. ### Rendering
    **Fast Thumbnail renderer**
    - `scripts/render.py` Open3D triangle mesh visualization with headless rendering, which generates an 200x150 thumbnail image of reconstruted mesh.  
    **Quality Driven Stochastic Ray Tracing Renderer**
    - `scripts/mts_render.py` To generate more visually appealing rendering results, we use Mitsuba2 renderer to render a 1920x1440 image of the reconstruted mesh. `thumbnail.sh` can be used to generating thumbnails from rendered image.


- `start_process_server.py` - Starts the scan processing server. The main entry point is at `process.py`.  Running this starts the upload server on port 5000, simple flask server that only handles one request at a time (will block until scan is processed).
- `scan_processor.py` - Main scan processing script.  Edit to see/change path for tools/applications.
 
## Indexing scripts

Indexing scripts are used to collate information about the scans and index them.
- `monitor.py` - Web service entry point for monitoring and triggering of indexing of scans.  Run `python monitor.py` to start the monitor server on port 5001 (simple flask server).
- `index.py` - Creates index of scans in a directory and outputs a csv file
- `scripts/index_scannet.sh` - Index both staging and checked scans and updates WebUI db

## Statistics computation scripts

- `compute_annotation_stats.py` - Compute aggregated annotation statistics
- `compute_timings.py` - Compute processing times for scans
- `scripts/combine_stats.py` - Combines statistics with index


## Configuration files

- `scannet.json` - Metadata for ScanNet assets for use with the Scene Toolkit viewer
- `scan_stages.json` - The stages of the scan pipeline (so we can track progress)
- `upload.ini` - Configuration file for upload server

## Setup Staging Server

```bash 
./start_upload_server.sh    # Start the upload server, recieve files from scanner app
./start_process_server.sh   # Start the process server, recieve process request from web-ui
./monitor.py or python monitor.py   # Web service entry point for monitoring and triggering of indexing of scans.
 ```