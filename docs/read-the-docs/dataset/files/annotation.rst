Annotation Data
===============

In MultiScan dataset, the annotations includes the 1. Semantic: semantic annotation of objects and parts, 2. OBB: semantically-oriented bounding boxes with defined front and up axis for each object, 3. Motion: motion annotation for the articulated objects.

The object and part labels in MultiScan dataset following the form `object_label:part_label = object_category.object_index:part_category.part_index`. For example, a bag without parts is named ``bag.1``, a door with parts ``door`` and ``door_frame`` has the labels ``door.1:door.1`` and ``door.1:door_frame.1``.

Object and part labels, semantic OBB annotations and motion annotations are stored in the `scanId.annotations.json` file. The per face(triangle) semantic object ID and part ID are stored in the `scanId.ply` with two face properties `objectId` and `partId`.

scanId.annotations.json
-----------------------

Following is an example MultiScan annotation data extracted from `scene_00000_00.annotations.json`_.

.. _annotation_data_example:

.. code-block:: json

    {
        "version": "multiscan@0.0.1",
        "scanId": "scene_00000_00",
        "objects": [
            {
                "objectId": 1,
                "label": "wall_cabinet.1",
                "mobilityType": "fixed",
                "partIds": [1, 10, 11, 12, 13, 17, 18, 2, 3, 4, 5, 6, 7, 8, 9, 19],
                "obb": {
                    "centroid": [-0.8508913650584475, 1.0251899118089505, -0.015568494796752987],
                    "axesLengths": [3.063295787372859, 2.6116669178009033, 0.3565280712856653],
                    "normalizedAxes": [-0.9975306109909383, -0.07023304162604237, -1.5594867980537856e-17, 0, -2.220446049250313e-16, 1, -0.07023304162604234, 0.9975306109909383, 2.21496290418108e-16],
                    "min": [-2.3912770497061846, 0.7397937891427258, -1.3214019536972046],
                    "max": [0.6894943195892895, 1.3105860344751752, 1.2902649641036987],
                    "front": [0.07023304162604234, -0.9975306109909383, -2.21496290418108e-16],
                    "up": [0, -2.220446049250313e-16, 1]
                }
            },
            {
                "objectId": 2,
                "label": "bag.1",
                "mobilityType": "movable",
                "partIds": [
                    14
                ],
                "obb": {
                    "centroid": [0.09693120858653177, 0.9104652242483331, -0.6495804935693742],
                    "axesLengths": [0.2522365669610245, 0.33283099532127386, 0.15902812283054288],
                    "normalizedAxes": [0.9861942396120026, 0.16559263798884283, 3.6768951880726337e-17, 0, -2.220446049250313e-16, 1, 0.16559263798884283, -0.9861942396120026, -2.1897911031398878e-16],
                    "min": [-0.040612859278664634, 0.8111646556522747, -0.8159959912300112],
                    "max": [0.23447527645172817, 1.0097657928443915, -0.48316499590873724],
                    "front": [0.16559263798884283, -0.9861942396120026, -2.1897911031398878e-16],
                    "up": [0, -2.220446049250313e-16, 1]
                }
            }
        ],
        "parts": [
            {
                "partId": 1,
                "label": "door.1",
                "articulations": [
                    {
                    "type": "rotation",
                    "origin": [-1.4811853829377406, 0.8572279858589172, 0.9886049665923767],
                    "state": 0,
                    "axis": [0.02977539182170522, 0, -0.9995566147256812],
                    "rangeMin": 0,
                    "rangeMax": 1.5707963267948966,
                    "isClosed": true
                    }
                ],
                "parentId": 19
            },
            {
                "partId": 14,
                "label": "bag.1"
            },
            {
                "partId": 19,
                "label": "wall_cabinet.1"
            },
        ]
    }

.. _annotation_data_version:

.. option:: version (string)

    A string describes the current version of the MultiScan dataset

.. _annotation_data_scanId:

.. option:: scanId (string)

    The corresponding scan ID of the annotation data, following the naming convention `scanId = scene_xxxxx_xx`, where ``xxxxx`` is a number string with leading zeros represents the index of the scene, ``xx`` is a number string with leading zeros represents the index of the scan.

.. _annotation_data_objects:

objects
~~~~~~~

.. _annotation_data_objects_objects:

.. option:: objects (list: dict)

    A list of ``dict``, where each ``dict`` contains the info of an annotated object. The info includes |annotation_data_objects_object_id|_, |annotation_data_objects_label|_, |annotation_data_objects_part_ids|_, |annotation_data_objects_mobility_type|_ and |annotation_data_objects_obb|_.

.. _annotation_data_objects_object_id:

.. option:: objects.objectId (string)

    The ID of the annotated object, it is the index + 1 of the object in the |annotation_data_objects_objects|_ list.

.. _annotation_data_objects_label:

.. option:: objects.label (string)

    The label (`object_label`) of the annotated object, following the naming convention: `object_label = object_category.object_index`.

.. _annotation_data_objects_part_ids:

.. option:: objects.partIds (list: int)

    A list of part IDs (`partIds`) of the annotated parts belong to the labeled object, the annotations of this part can be found in the `parts` with the matching `partId`. If the object has no children parts, the object is considered as has only 1 part, and the part is labeled the same as the object label.

.. _annotation_data_objects_mobility_type:

.. option:: objects.mobilityType (string)

    The object mobility type, which is on of the type in [`arch`, `fixed`, `movable`].

.. _annotation_data_objects_obb:

.. option:: objects.obb (dict)

    A dictionary contains the data of the annotated semantically-oriented bounding boxes (OBB). The OBB is in the 3D world coordinate system that the scan is currently in. The OBB has following attributes: `centroid`, `axesLengths`, `normalizedAxes`, `min`, `max`, `front`, `up`.

.. _annotation_data_objects_obb_centroid:

.. option:: objects.obb.centroid (list: float)

    A 3x1 float vector `[x, y, z]` represents the 3D position of the OBB centroid.

.. _annotation_data_objects_obb_axesLengths:

.. option:: objects.obb.axesLengths (list: float)

    A 3x1 float vector represents the full side lengths of the OBB, the direction of each side is defined in |annotation_data_objects_obb_normalizedAxes|_.

.. _annotation_data_objects_obb_normalizedAxes:

.. option:: objects.obb.normalizedAxes (list: float)

    A 9x1 float vector represents the column major 3x3 rotation matrix, where each of the columns represent one of the normalized axes (with vector length 1) of the oriented bounding box. Each `axis` has 3 float numbers ``xyz`` defines the direction of the OBB edges.

.. _annotation_data_objects_obb_min:

.. option:: objects.obb.min (list: float)

    A 3x1 float vector represents the min bounds for geometry coordinates, which is one of the corner points in the OBB with minimum xyz positional values.

.. _annotation_data_objects_obb_max:

.. option:: objects.obb.max (list: float)

    A 3x1 float vector represents the max bounds for geometry coordinates, which is one of the corner points in the OBB with maximum xyz positional values.

.. _annotation_data_objects_obb_front:

.. option:: objects.obb.front (list: float)

    A 3x1 float vector represents the normalized front direction of the object. The front axis should be parallel to one of the axes stored in |annotation_data_objects_obb_normalizedAxes|_.

.. _annotation_data_objects_obb_up:

.. option:: objects.obb.up (list: float)

    A 3x1 float vector represents the normalized up direction of the object. The up axis should be parallel to one of the axes stored in |annotation_data_objects_obb_normalizedAxes|_.

.. todo::

    Add figures and highlights for the visualizing the geometric meaning for the obb attributes

parts
~~~~~~~~~~~~~

.. _annotation_data_parts_parts:

.. option:: parts (list: dict)

    A list of ``dict``, where each ``dict`` contains the info of an annotated part. The info includes |annotation_data_parts_part_id|_, |annotation_data_parts_label|_, |annotation_data_parent_id|_, |annotation_data_articulations|_.

.. _annotation_data_parts_part_id:

.. option:: parts.partId (string)

    The ID of the annotated part, it is the index + 1 of the part in the |annotation_data_parts_parts|_ list.

.. option:: parts.label (string)

    The label (`part_label`) of the annotated part, following the naming convention: `part_label = part_category.part_index`.

.. option:: parts.parentId (string)

    The |annotation_data_parts_part_id|_ of the parent part. If the part is the root part, it will not have this property.

.. _annotation_data_articulations:

.. option:: parts.articulations (list: dict):

    A list of annotated annotations the part has.

.. _annotation_data_articulations_type:

.. option:: parts.articulations.type (string)

    The articulation type of the movable part. There are 2 types of the articulation: ``rotation``, ``translation``.

    For the movable parts with motion type ``rotation``, the part rotate around the annotated joint with the range `[rangeMin, rangeMax]`.

    For the movable parts with motion type ``translation``, the part translate along the annotated joint with the range `[rangeMin, rangeMax]`.

.. _annotation_data_articulations_origin:

.. option:: parts.articulations.origin (list: float)

    A 3x1 float vector represents the joint origin position, which is the anchor point of the joint and defines the starting position of the joint. The joint origin is in the 3D world coordinate system that the scan is currently in.

.. _annotation_data_articulations_axis:

.. option:: parts.articulations.axis (list: float)

    A 3x1 float vector represents the normalized joint direction (with vector length 1). The joint starts from the `origin` and pointing towards the direction defined by `axis`.

.. _annotation_data_articulations_rangeMin:

.. option:: parts.articulations.rangeMin (float)

    The minimum range of the motion that the movable part can reach relative to the current `state`. The unit is ``radians`` for the ``rotation`` type motion, The unit is ``m (meter)`` for the ``translation`` type motion.

.. _annotation_data_articulations_rangeMax:

.. option:: parts.articulations.rangeMax (float)

    The maximum range of the motion that the movable part can reach relative to the current `state`. The unit is ``radians`` for the ``rotation`` type motion, The unit is ``m (meter)`` for the ``translation`` type motion.

.. _annotation_data_articulations_state:

.. option:: parts.articulations.state (float)

    The current state of the movable part. The `state` value is within the range `[rangeMin, rangeMax]`.

.. _annotation_data_articulations_isClosed:

.. option:: parts.articulations.isClosed (bool)

    A boolean value defines whether the movable part is in the closed state. Parts with `state` value smaller than the threshold ``0.1`` is considered closed.


.. _Mesh with vertex color and per face semantics:

Mesh with vertex color and per face semantics
----------------------

    Mesh with same geometry as the textured mesh, but has vertex colors instead of UV mapped textures. This mesh file is stored in `scene_xxxxx_xx.ply` in PLY binary format. The mesh has attributes `vertices`, `vertex normals`, `vertex colors`, `faces`, `objectId`, `partId`. Following is an example of the ASCII version of the ply header in the mesh:

    .. code-block:: text

        ply
        format binary_little_endian 1.0
        comment VCGLIB generated
        element vertex 150014
        property double x
        property double y
        property double z
        property double nx
        property double ny
        property double nz
        property uchar red
        property uchar green
        property uchar blue
        property uchar alpha
        element face 295662
        property list uchar int vertex_indices
        property ushort objectId
        property ushort partId
        end_header

    Use the per face `objectId` and `partId` to find the annotations of the objects and parts in the `scanId.annotations.json`_.

.. |annotation_data_objects_objects| replace:: `objects`
.. |annotation_data_objects_object_id| replace:: `objectId`
.. |annotation_data_objects_label| replace:: `label`
.. |annotation_data_objects_part_ids| replace:: `partIds`
.. |annotation_data_objects_obb| replace:: `obb`
.. |annotation_data_objects_mobility_type| replace:: `mobilityType`
.. |annotation_data_objects_obb_normalizedAxes| replace:: `normalizedAxes`

.. |annotation_data_parts_part_id| replace:: `partId`
.. |annotation_data_parts_label| replace:: `label`
.. |annotation_data_parent_id| replace:: `parentId`
.. |annotation_data_articulations| replace:: `articulations`

.. _scene_00000_00.annotations.json: ../../_static/dataset/scene_00000_00.annotations.json