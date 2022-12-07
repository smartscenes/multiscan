MultiScan Code Structure
========================

Overview
--------

.. code-block:: bash
    
    ├── config/
    │   ├── config.yaml # configuration file for the pipeline
    │   └── reconstruction/ # configuration file for the RGB-D integration reconstruction
    ├── docs/
    │   ├── figures/
    │   └── *.md # README files explaining the details, such as install instruction, etc 
    ├── benchmarks/
    │   ├── config/ # config for the data preparation
    │   ├── methods/
    │   │   ├── PointGroup summodule
    │   │   ├── SSTNet summodule
    │   │   ├── HAIS summodule
    │   │   ├── patches/ # git patches for the included methods
    │   │   └── shape2motion-pytorch summodule
    │   ├── consistency-eval/ # instance segmentation consistency evaluation
    │   ├── data-perpare/ # script transfer the anonymous data to hdf5 format, and scripts transfer the hdf5 format data to methods dependent data
    │   ├── data-statistics/ # scripts to get data statistics and plots
    │   ├── multiscan-labels-hierarchy.csv
    │   └── multiscan-benchmark-labels.csv
    ├── server/ # multiscan staging and processing server
    ├── web-ui/
    │   ├── web-client/ # web front-end UI
    │   └── web-server/ # web backend-end server, listen to signals from front-end, and sent signals to the multiscan server
    ├── segmentator/ # graph based mesh segmentation
    ├── scanner/ # android and ios scanner app
    ├── multiscan/
    │   ├── meshproc/ # basic mesh processing
    │   ├── utils/ # utility functions
    │   └── visual/ # mesh visualizations
    ├── dependencies/
    │   ├── open3d summodule
    │   ├── instant-meshes summodule
    │   ├── mvs-texturing summodule
    │   └── patches/
    │── CMakeLists.txt
    │── setup.cfg
    │── setup.py
    │── LICENSE
    │── requirements.txt
    └── README.md
