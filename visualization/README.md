# Data Visualization

## Annotations Visualization

There are 3 types of annotations in MultiScan: semantic label annotation, semantic OBB annotation, articulation annotation.  
Script [annotation_visualize.py](annotation_visualize.py) generates turntable videos for the 3 annotations motioned above, with an additional video for the textured mesh of the scan.

### Run

```bash
python annotation_visualize.py input_dir=<path to downloaded dataset folder contains the scans> output_dir=<path to output folder will contain turntable videos>
```
Add additional argument `scenes='["scene_00021","scene_00022"]'` to generate visualizations for only these 2 unique scenes (by default, the script generates visualizations for all the downloaded scans). Or change parameters in the [config](config/config.yaml) file.

### Outputs
```
outputs
├── scene_xxxxx_xx
│   ├── scene_xxxxx_xx.articulation.mp4
│   ├── scene_xxxxx_xx.instance.mp4
│   ├── scene_xxxxx_xx.obb.mp4
│   └── scene_xxxxx_xx.textured.mp4
...
```
