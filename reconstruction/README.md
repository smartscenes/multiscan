# RGB-D Reconstruction Pipeline

With apple's LiDAR sensors and ARKit framework, we can aquire RGB color stream, depth stream, confidence maps and camera information of each frame including camera transformation at each frame. 

### Reconstruction with known camera poses
Camera poses are available from ARKit API for all the captured frames. We don't need to estimate the camera poses.  
Directorily apply volume integration and mesh extraction.
1. Using TSDF volume integration to compute the volume of the scan and marching cubes to extract the triangle mesh.

### Postprocessing
The extracted triangle mesh will be cleaned by Meshlab, which includes remove duplicated faces and vertices, remove zero area faces, repair non manifold edges by removing faces, remove isolated pieces. After the cleaning, the mesh will be decimated by Instant Meshes, the decimtated mesh will be saved in `<filename>_decimated.ply`. The decimated mesh will be aligned to normal world coordinates, the transformation will also be applied to raw `<filename>.ply` mesh. The pose of the original reconstructed mesh will be saved in  `<filename>-align-transform.json`.

## Dependencies
* Open3D 0.13.0
* Hydra 1.1
* Instant-meshes

## Configuration and Run
Configurable parameters are listed in [reconstruction.yaml](../config/reconstruction/reconstruction.yaml). 
With `hydra`, parameters can be overridden from the command line:
* Reconstruction with known camera poses
```bash
python main.py \
reconstruction.input.color_stream=path/to/scanID.mp4 or path/to/color_images \
reconstruction.input.depth_stream=path/to/scanID.depth.zlib or path/to/depth_images \
reconstruction.input.confidence_stream=path/to/scanID.confidence.zlib or None \
reconstruction.input.metadata_file=path/to/scanID.json \
reconstruction.input.trajectory_file=path/to/scanID.jsonl \
reconstruction.output.save_folder=path/to/staging/scanID
```

To accelerate the integration processm, `reconstruction.alg_param.integration.with_color` can be set to `false` and only depth frames will be used in the integration.

`hydra` also allows dynamic command line tab completion, you can enable tab completion via:
```
eval "$(python main.py -sc install=bash)" 
```
You can find more details about `hydra` [**here**](https://hydra.cc/docs/intro/)

