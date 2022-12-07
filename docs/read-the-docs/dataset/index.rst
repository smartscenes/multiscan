MultiScan Dataset
=================

File System Structure
---------------------

Each scan is named as `scene_xxxxx_xx`, the first 5 digits represent the scene ID, the last 2 digits represent the scan ID. In MultiScan, each scene is a unique indoor environment, scans records the multiple states of the scene at multiple time intervals. Take scene 00000 as an example, and it has 2 scans, the scan ID of these 2 scans are `scene_00000_00` and `scene_00000_01`.

.. code-block:: bash

    scene_xxxxx_xx/
        ├── scene_xxxxx_xx.annotations.json
        ├── scene_xxxxx_xx.align.json
        ├── scene_xxxxx_xx.ply
        ├── scene_xxxxx_xx.json
        ├── scene_xxxxx_xx.jsonl
        ├── scene_xxxxx_xx.mp4
        ├── scene_xxxxx_xx.depth.zlib
        ├── scene_xxxxx_xx.confidence.zlib
        └── textured_mesh/
            ├── scene_xxxxx_xx-tex0000.png
            ├── scene_xxxxx_xx-tex0001.png
            ├── ... more png atlas
            ├── scene_xxxxx_xx.mtl
            └── scene_xxxxx_xx.obj

Files
---------------------

.. list-table::
   :widths: 15 5 50
   :header-rows: 1
   :class: tight-table

   * - File Name
     - Group
     - Description
   * - scene_xxxxx_xx.json
     - Acquired
     - Data collection metadata.
   * - scene_xxxxx_xx.jsonl
     - Acquired
     - Acquired camera parameters for each frame: `timestamp`, `quaternion`, `intrinsics`, `transform`, `euler_angles`, `exposure_duration`.
   * - scene_xxxxx_xx.mp4
     - Acquired
     - Acquired RGB frames encoded with H.264 codec.
   * - scene_xxxxx_xx.depth.zlib
     - Acquired
     - Acquired depth stream with zlib compression, each depth frame has pixel size 16-bit float with depth values in meters.
   * - scene_xxxxx_xx.confidence.zlib
     - Acquired
     - Acquired confidence stream with zlib compression, each confidence frame has pixel size 8-bit unsigned int.
   * - scene_xxxxx_xx.obj
     - Output
     - Textured mesh in OBJ format, encodes the vertex coords, UV coords, vertex normals, faces.
   * - scene_xxxxx_xx.mtl
     - Output
     - Textured mesh material in MTL format, defines the material and lighting properties.
   * - scene_xxxxx_xx-tex00xx.png
     - Output
     - Texture atlas in PNG format, describes the suface texture of the mesh.
   * - scene_xxxxx_xx.align.json
     - Output
     - | 1. Transformation matrix used to align the reconstructed mesh to common coordinate frame.
       | 2. Transformation matrix align the current scan to the reference scan
   * - scene_xxxxx_xx.annotations.json
     - Annotation
     - Semantic, obb, articulation annotation results.
   * - scene_xxxxx_xx.ply
     - Annotation
     - Mesh in PLY format with vertex colors tranformed from the textured mesh and per face semantic annotations.

.. toctree::
    :maxdepth: 1
    :caption: Details

    files/acquired
    files/output
    files/annotation
