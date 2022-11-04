# Mesh Segmentation

We developed an annotation tool for specifying semantic annotation in texture space using Felzenswalb and Huttenlocher's [*Graph Based Image Segmentation*](https://cs.brown.edu/~pff/segment/index.html) algorithm on computed mesh normals. This will help reduce the effort of manual annotation.

## Build
Note: If you have followed instructions in [installation manual](../doc/INSTALL.md), the segmentator is already built. See below if you want to build the converter separately.

```bash
cmake -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX=path_to_binary_install_location -DBOOST_ROOT path_to_boost -DRAPIDJSON_DIR=path_to_rapidjson
make -j$(nproc)
make install
```

## Usage

```
./segmentator --$(arguments) $(values)
```

### Parameter

```bash
--help                              help message
--input arg                         set input mesh file
--kThresh arg (=0.00999999978)      set k threshold
--segMinVerts arg (=20)             set minimum segment size
--colorWeight arg (=0.5)            set weight for vertex colors
--colorKThresh arg (=0.00999999978) set k threshold in second stage
--colorSegMinVerts arg (=20)        set minimum segment size in second stage
--scanID arg (=default)             set the scan ID in the output json file
--output arg                        set the filepath of the output json file
```

### Output format
```json
{
    "id": "<scanID>",
    "version": "hierseg@0.0.1",
    "params": {
        "kThresh": 0.009999999776482582,
        "segMinVerts": 20,
        "colorWeight": 0.5,
        "colorKThresh": 0.009999999776482582,
        "colorSegMinVerts": 20
    },
    "hierarchies": [{
            "name": "fine-coarse",
            "levels": ["fine", "coarse"]
        }],
    "segmentation": [{
            "name": "fine",
            "elementType": "vertices",
            "index": []
        }, {
            "name": "coarse",
            "elementType": "vertices",
            "index": []
        }]
}
```
