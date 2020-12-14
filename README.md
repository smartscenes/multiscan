# MultiScan

Multiscan is a scalable framework that allows dense reconstruction of real-world indoor scenes with RGB or RGB-D sensors.
The user moves freely through an indoor scene to scan the environment, and uploads the scanning data to a staging server for scene mesh reconstruction.
A web interface allows browsing of the staged scanning data and initiating reconstruction, post-processing and annotation of the acquired environments.

-----------------------------------

## Scanner
The [Scanner App](scanner/ios) collects data using sensors on an Android/iOS device. User moves around holding the device with Scanner app installed to scan the scene. Once the scanning completed, users can upload the data to the staging server. The Scanner App has three modes, single camera, dual camera and RGB-D. (We currently only support IOS device with the single camera mode and the RGB-D mode, and the dual camera mode is not completed and still in progress.)


-----------------------------------

## Staging Server
The [staging server](server) has 3 main functionalities:

1. Stage uploaded scans by the devices (iPhone or iPad) and trigger scan processing. To ensure that scans can be automatically processed, the scans should be placed in a directory with lots of space and accessible to the scanning processor.
2. Process staged scans. Handle reconstruction processing request from Web-UI, when user press interactive buttons on Web-UI.
3. Index staged scans. Go through scan folders and collate information about the scans.

### Staging Data Formats
```shell
<scanId>
----------------------------------------------------------------------
Data uploaded by scanner app

|-- <scanId>.json
    Meta data of uploaded scan, such as the resolution of RGB and depth stream, number of captured frames, etc.
|-- <scanId>.jsonl
    Camera informations of each frame, including timestamp, intrinsics, camera transform, euler angles and exposure duration
|-- <scanId>.depth.zlib
    Compressed depth stream with resolution 256x192, containing depth values of captured frames
|-- <scanId>.confidence.zlib
    Compressed confidence maps with resolution 256x192, containing confidence level of depth frames
|-- <scanId>.mp4
    RGB color stream, resolution can vary based on different modes in Scanner App
----------------------------------------------------------------------
Data generated by server

|-- <scanId>_preview.mp4
    Compressed RGB color stream with resolution 320x240
|-- <scanId>_thumb.jpg
    A 200x150 RGB frame extracted from <scanId>.mp4
|-- <scanId>_o3d_thumb.png
    A 200x150 RGB rendering result of reconstructed mesh using Open3D triangle mesh renderer
|-- <scanId>_mts.png
    A 1920x1440 RGB rendering result of reconstructed mesh using Mitsuba2 renderer
|-- <scanId>.ply
    Reconstructed mesh of uploaded scan
|-- <scanId>_cleaned.ply
    Mesh after mesh topology cleanup and decimation
```
-----------------------------------

## Web-UI

The [Web-UI](web-ui) is an interactive interface for providing an overview of staged scan data, managing scan data, and controlling the reconstruction and mesh annotation pipeline.

-----------------------------------

## Reconstruction

### Open3D RGB-D Reconstruction Pipeline 
When a depth sensor is available, RGB-D data can be acquired.
We use the [Open3D](dependencies/Open3D) RGB-D reconstruction pipeline to produce 3D mesh reconstructions.

### Meshroom RGB Photogrammetric Reconstruction Pipeline
When only RGB data is available, the [Meshroom](dependencies/meshroom) photogrammetry pipeline based on structure from motion (SfM) and multi-view stereo (MVS) reconstruction is used.

-----------------------------------

## Post Processsing

### Mesh Topology Cleanup and Decimation
We use [Instant-Meshes](instant-meshes) for this task.
The default reconstructed mesh using marching cubes from the Open3D RGB-D reconstruction pipeline usually contains millions of vertices and faces for a single bedroom, which makes it hard for mesh annotation and segmentation.
An additional mesh topology cleanup and decimation step is performed to reduce mesh complexity, and keep geometry unchanged as much as possible.

### Segmentation
[Segmentor](https://github.com/ScanNet/ScanNet/tree/master/Segmentator) from ScanNet is used for mesh segmentation.
The mesh segmentation algorithm uses Felzenswalb and Huttenlocher's Graph Based Image Segmentation algorithm on computed mesh normals.
The segments are used to carry out semantic annotation of the 3D mesh so that objects and their parts can be extracted.

### Rendering

#### Fast Thumbnail renderer
Open3D triangle mesh visualization with headless rendering, which generates an 200x150 thumbnail image of reconstruted mesh.  

#### High Quality Ray Tracing Renderer
To generate more visually appealing rendering results, we use Mitsuba2 renderer to render a 1920x1440 image of the reconstruted mesh.  

## Semantic Annotation

### Object and object part segmentation, and articulation annotation

We use a web-based UI implemented using the [SmartScenes toolkit](https://github.com/smartscenes/sstk) codebase to annotate individual 3D object instances and their parts.
Once objects and their parts are annotated, we then specify articulation parameters for object parts.
Specifically, we utilize the [ScanAnnotator](https://github.com/smartscenes/sstk/blob/master/client/js/apps/scan-net/ScanAnnotator.js) web app to carry out this annotation.

-----------------------------------
## Build Platform
Tested on Ubuntu 16.04 Linux machine with Intel(R) Core(TM) i9-9900K CPU @ 3.60GHz, 32GB RAM, GeForce RTX 2080 Ti.

Tested on Ubuntu 20.04 Linux machine with AMD Ryzen 7 3700X 8-Core Processor, 16GB RAM, GeForce RTX 2060 SUPER.

-----------------------------------

## References

Our work is built on top of the ScanNet dataset acquisition framework, Open3D, and Meshroom for 3D reconstruction.
We use the Mitsuba2 Renderer and Instant Meshes for rendering and post-processing.

    @misc{dai2017scannet,
      title={ScanNet: Richly-annotated 3D Reconstructions of Indoor Scenes}, 
      author={Angela Dai and Angel X. Chang and Manolis Savva and Maciej Halber and Thomas Funkhouser and Matthias Nießner},
      year={2017},
      eprint={1702.04405},
      archivePrefix={arXiv},
      primaryClass={cs.CV}
    }

    @article{Zhou2018,
        author    = {Qian-Yi Zhou and Jaesik Park and Vladlen Koltun},
        title     = {{Open3D}: {A} Modern Library for {3D} Data Processing},
        journal   = {arXiv:1801.09847},
        year      = {2018},
    }

    @article{NimierDavidVicini2019Mitsuba2, 
        author = {Merlin Nimier-David and Delio Vicini and Tizian Zeltner and Wenzel Jakob}, 
        title = {Mitsuba 2: A Retargetable Forward and Inverse Renderer}, 
        journal = {Transactions on Graphics (Proceedings of SIGGRAPH Asia)},
        volume = {38},
        number = {6},
        year = {2019},
        month = dec,
        doi = {10.1145/3355089.3356498}
    }

    @Misc{Meshroom,
        author = {AliceVision},
        title = {{Meshroom: A 3D reconstruction software.}},
        year = {2018},
        url = {https://github.com/alicevision/meshroom}
    }

    @article{10.1145/2816795.2818078,
        author = {Jakob, Wenzel and Tarini, Marco and Panozzo, Daniele and Sorkine-Hornung, Olga},
        title = {Instant Field-Aligned Meshes},
        year = {2015},
        issue_date = {November 2015},
        publisher = {Association for Computing Machinery},
        address = {New York, NY, USA},
        volume = {34},
        number = {6},
        issn = {0730-0301},
        url = {https://doi.org/10.1145/2816795.2818078},
        doi = {10.1145/2816795.2818078},
        journal = {ACM Trans. Graph.},
        month = oct,
        articleno = {189},
        numpages = {15},
}
