Output Data from Processing Server
==================================

Scans collected by the Scanner App are uploaded to the processing server for performing tasks that require heavy computational resources, such as reconstruction, texturing, unsupervised segmentation. Following are the output data from the processing server and their formats:

* Textured mesh: `scene_xxxxx_xx.obj`, `scene_xxxxx_xx.mtl`, `scene_xxxxx_xx-tex00xx.png`
* Mesh with vertex color: `scene_xxxxx_xx.vertex_color.ply`
* Scan alignment file: `scene_xxxxx_xx.align.json`

.. _Textured mesh:

Textured mesh
-------------

scene_xxxxx_xx.obj
    Textured mesh with UV mapping in OBJ format, encodes the vertex positions, UV coords, vertex normals, faces. The textured mesh is aligned with z-axis as the up direction, and the floor of the scan is aligned to the xy plane.

scene_xxxxx_xx.mtl
    Textured mesh material in MTL format, defines the material and lighting properties. The attribute ``map_Kd`` is linked to the texture atlas files with the relative path to the ``mtl`` file.

scene_xxxxx_xx-tex00xx.png
    The texture atlas file specifies the diffuse color texture of the faces in the mesh. The texture atlas are in 4K resolution (3840 x 2160 pixel) stored in PNG format. ``00xx`` is a number string with leading zeros specifies the index of the texture atlas.


Scan alignment file
-------------------

example `scene_00000_01.align.json`

.. _scan_alignment_example:

.. code-block:: json

    {
      "version": "multiscan@0.0.1",
      "coordinate_transform": [-0.8714070984354318, -1.0892632704258717e-16, -0.4905605658798324, 0.0, -0.4905605658798324, 1.9349124490096333e-16, 0.8714070984354318, 0.0, 0.0, 1.0, -2.220446049250313e-16, 0.0, -1.9023691915882401, -0.003235161304473723, 2.192399906387362, 1.0],
      "reference_scan_alignment": {
        "target_id": "scene_00000_00",
        "transformation": [0.9953843464504538, 0.09592694187358794, -0.002832783822291686, 0.0, -0.09592861631675767, 0.9953881092826349, -0.00046094499897401443, 0.0, 0.0027755022887538624, 0.0007305624689502921, 0.99999588142428, 0.0, -0.3443665199336438, 0.07590382138298372, -0.0037171331536487557, 1.0]
      }
    }

.. _scan_alignment_version:

.. option:: version (string)

    A string describes the current version of the MultiScan dataset

.. _scan_alignment_coordinate_transform:

.. option:: coordinate_transform (list: float)

    The stored meshes in the MultiScan dataset are post processed with the alignment to a predefined 3D common coordinate frame. Where the the z-axis is the up direction, and the floor of the scan is aligned to the xy plane. The camera poses in the camera parameters file `scene_xxxxx_xx.jsonl` are unaligned, and `coordinate_transform` is used to transform the stored meshes back to the original unaligned poses in the same world space as the cameras in the camera parameters file.

    `coordinate_transform` is 16x1 vector corresponds to the column major 4x4 6 DoF transformation matrix that transforms the stored meshes to the original 3D coordinates after the reconstruction without alignment.

    The following example code shows how to use the `coordinate_transform`:

    .. code-block:: python

        import numpy as np
        import trimesh

        # load the scan mesh with vertex color
        mesh = trimesh.load('/path/to/scene_xxxxx_xx.vertex_color.ply')
        # coordinate_transform is the 16x1 vector
        transformation_mat = np.reshape(coordinate_transform, (4, 4), order='F')
        # apply inplace transformation, the mesh is transformed back to the pose without alignment
        mesh.apply_transform(transformation)

.. _scan_alignment_reference_scan_alignment:

.. option:: reference_scan_alignment (dict)

    The alignment information from the current scan to the reference scan. The alignment information is stored as JSON data with attributes `target_id` and `transformation`.

.. _scan_alignment_reference_scan_alignment_target_id:

.. option:: reference_scan_alignment.target_id (string)

    A string indicate the ID of the reference scan, which shares in the same scene but with different object states comparing to the current scan.

.. _scan_alignment_reference_scan_alignment_transformation:

.. option:: reference_scan_alignment.transformation (list: float)

    A 16x1 vector corresponds to the column major 4x4 6 DoF transformation matrix, that aligns the current scan to the reference scan. The scan ID of the reference scan is stored in `target_id`.

    By applying this transformation matrix, the reconstructed mesh of the scan can be aligned to the mesh of the reference scan, where most of the unmoved objects and room architectures will be overlapping.

    The following example code shows how to use the `transformation`:

    .. code-block:: python

        import numpy as np
        import trimesh

        # load the scan mesh with vertex color
        mesh = trimesh.load('/path/to/scene_xxxxx_xx.vertex_color.ply')
        # transformation is the 16x1 vector
        transformation_mat = np.reshape(transformation, (4, 4), order='F')
        # apply inplace transformation, the mesh is now aligned the reference scan
        mesh.apply_transform(transformation)
