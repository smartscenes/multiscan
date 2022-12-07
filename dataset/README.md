# Benchmark Dataset Process

Download and copy MultiScan benchmark dataset [download script](https://forms.gle/YuE2gZTMSBoJiLDh7) to `[PROJECT_ROOT]/dataset` directory, and follow the instructions bellow to dowload the MultiScan benchmark dataset:

## Object Instance Segmentation

Preprocessed object instance segmentation data download:
```bash
./download_benchmark_dataset.sh -o <output_dir>
```

Run dataset process from Multiscan Dataset:
```bash
python gen_instsegm_dataset.py input_path=/path/to/multiscan_dataset output_path=<object_instance_segmentation output_dir>
```

## Articulated Objects

Part instance segmentation and Mobility prediction both take articulated objects as inputs. To ensure the consistency of data used in part instance segmentation benchmark and mobility prediction benchmark, we first extract the articulated objects in the MultiScan dataset to HDF5 files, then have scripts convert the HDF5 files to various formats required by the methods.

Preprocessed articulated objects dataset download:
```bash
./download_benchmark_dataset.sh -a <output_dir>
```

Run dataset process from Multiscan Dataset:
```bash
python gen_articulated_dataset.py input_path=/path/to/multiscan_dataset output_path=<articulated_dataset output_dir>
```

## Part Instance Segmentation

Preprocessed part instance segmentation data download:
```bash
./download_benchmark_dataset.sh -p <output_dir>
```

Run dataset process from Multiscan Dataset:
```bash
python gen_partsegm_dataset.py input_path=<articulated_dataset output_dir> output_path=<part_instance_segmentation output_dir>
```

## Mobility Prediction

**Shape2Motion input dataset**

Preprocessed shape2motion input data download:
```bash
./download_benchmark_dataset.sh -s <output_dir>
```

Run dataset process from Multiscan Dataset:  
Coming soon.

**OPDPN input dataset**

Preprocessed opdpn input data download:
```bash
./download_benchmark_dataset.sh -n <output_dir>
```

OPDPN datset generation code requires [dgl](https://www.dgl.ai/) library. Please install dgl via pip:
```bash
pip install dgl==0.6.0
```
Run dataset process from Multiscan Dataset:
```bash
python gen_partsegm_dataset.py input_path=<articulated_dataset output_dir> output_path=<part_instance_segmentation output_dir>
```

