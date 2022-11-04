Benchmark Dataset
=================

Scene Level
-----------

Object Instance Segmentation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Object Instance Segmentation takes `{scan_id}_inst_nostuff.pth` as inputs in the training phase. During the evaluation, both `{scan_id}_inst_nostuff.pth` and `{scan_id}.txt` are token as inputs, where `{scan_id}.txt` is the GT object instance segmentation mask.

**Input**

{scan_id}_inst_nostuff.pth
    .. option:: coords (numpy array: float32):

        (N,3) array of xyz coordinates of the scene point cloud. The coords are zero centered, such that the centroid of the point cloud is shifted to the zero origin.

    .. option:: colors (numpy array: float32):

        (N,3) array of vertex colors of the scene point cloud. With color linearly normalized to range `[-0.5, 0.5]`.

    .. option:: normals (numpy array: float32):

        (N,3) array of vertex normals of the scene point cloud.

    .. option:: sem_labels (numpy array: int32):

        Object semantic IDs of the points in the scene point cloud.

    .. option:: instance_ids (numpy array: int32):

        Object instance IDs of the points in the scene point cloud.

**GT Labels**

{scan_id}.txt
    Ground truth object instance segmentation of the scene in the ``.txt`` format. The column of the ``.txt`` GT object instance segmentation file is the instance ID of each point.

Object Level
------------
Part Instance Segmentation and Mobility Estimation both take articulated objects as inputs. To ensure the consistency of data used in Part Instance Segmentation Benchmark and Mobility Estimation Benchmark, we first extract the articulated objects in the MultiScan Dataset to a single HDF5 file, then have scripts convert this HDF5 file to various formats required by the methods.

Articulated Objects HDF5
~~~~~~~~~~~~~~~~~~~~~~~~

.. _group_name:

**HDF5 Groups**
    Each group in the HDF5 file stores the data of 1 articulated object. The group name is formatted as `group_name = {scan_id}_{object_id}`. Where `scan_id` is defined here, `object_id` is the object semantic annotation label `object_category.object_index`

**HDF5 Attributes**

.. _object_name:

    .. option:: object_name (string):

        Semantic name of the object. The semantic name is the grouped object category used in scene level object instance segmentation.

.. _num_parts:

    .. option:: num_parts (int):

        Number of movable parts in the articulated object.

    .. option:: has_additional_vertices (bool):

        A boolean signal indicates whether the extracted object has number of points greater than threshold 4096. If the object has fewer 4096 points, additional point up-sampling is applied to ensure each articulated object has least 4096 points.

**HDF5 Datasets**

.. _pts:

    .. option:: pts (numpy array: float32):

        (N,9) array of points of the object point cloud with xyz, rgb, normals. The object is aligned by fitting the annotated OBB to the common coordinate frame, with y axis is the up direction.

.. _faces:

    .. option:: faces (numpy array: float32):

        (N,3) array of the faces of the object triangle mesh.

.. _part_semantic_masks:

    .. option:: part_semantic_masks (numpy array: int32):

        (N,1) array, values are the part semantic IDs.

.. _part_instance_masks:

    .. option:: part_instance_masks (numpy array: int32):

        (N,1) array of point class in range [0, K] of N points. Value 0 represents the static part, value 1~K represents the K movable parts.

.. _motion_types:

    .. option:: motion_types (numpy array: float32):

        (K,1) array of the joint types corresponding to the K movable parts. Rotation: 0, translation: 1.

    .. option:: motion_origins (numpy array: float32):

        (K,3) array, positions of the K joint origins.

    .. option:: motion_axes (numpy array: float32):

        (K,3) array, directions of the K joint axes.

    .. option:: motion_ranges (numpy array: float32):

        (K,2) array, The ranges of the motion that the movable part can reach relative to the current `state`. The unit is ``radians`` for the ``rotation`` type motion, The unit is ``m (meter)`` for the ``translation`` type motion.

    .. option:: motion_states (numpy array: float32):

        (K,1) array, The current states of the K movable part.

.. _part_closed:

    .. option:: part_closed (numpy array: bool):

        (K,1) array, indicates whether part k is closed.

.. _transformation_back:

    .. option:: transformation_back (numpy array: float32):

        (16,1) column major transformation matrix transform the object back to origin pose in the scene before the canonical alignment.

.. _additional2original_vertex_match:

    .. option:: additional2original_vertex_match (numpy array: int32):

        Mapping from additionally up-sampled points to the index of the vertex in the originally extracted object.

Part Instance Segmentation
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Input**

    .. option:: key (string):

        same as the :ref:`group_name`.

    .. option:: object_name (string):

        same as the :ref:`object_name`.

    .. option:: coords (numpy array: float32):

        (N,3) array of xyz coordinates of the object point cloud.

    .. option:: colors (numpy array: float32):

        (N,3) array of vertex colors of the object point cloud.

    .. option:: normals (numpy array: float32):

        (N,3) array of vertex normals of the object point cloud.

    .. option:: faces (numpy array: float32):

        same as the :ref:`faces`.

    .. option:: sem_labels (numpy array: float32):

        same as :ref:`part_semantic_masks`.

    .. option:: instance_ids (numpy array: float32):

        same as :ref:`part_instance_masks`.

    .. option:: part_closed (numpy array: bool):

        same as :ref:`part_closed`.

    .. option:: transformation_back (numpy array: float32):

        same as :ref:`transformation_back`.

    .. option:: additional2original_vertex_match (numpy array: float32):

        same as :ref:`additional2original_vertex_match`.

**GT Labels**

    Ground truth part instance segmentation of the object in the ``.txt`` format. The first column of the ``.txt`` GT part instance segmentation file is the instance ID of each point, the second column indicates whether the points of the part is closed.

Mobility Estimation
~~~~~~~~~~~~~~~~~~~

Shape2Motion
************

**HDF5 Groups**

**HDF5 Attributes**

    .. option:: num_parts (int):

        same as the :ref:`num_parts`.

    .. option:: fps_sample (bool):

        Objects with more than 4096 points are down-sampled to 4096 points with FPS(Farthest Point Sampling) method. This boolean attribute indicates whether the object is down-sampled or not.

    .. option:: object_name (string):

        same as the :ref:`object_name`.

**HDF5 Datasets**

    .. option:: input_pts (numpy array: float32):

        same as the :ref:`pts`.

    .. option:: anchor_pts (numpy array: float32):

        (N, 1) array of the mask of the selected points in the object point cloud that is a set of closest points to the joint origin. 1 indicates the point is anchor point, 0 otherwise.

    .. option:: joint_direction_cat (numpy array: float32):

        (N, 1) array of the indices of the joint direction categories.

    .. option:: joint_direction_reg (numpy array: float32):

        (N, 3) array of joint direction from 14 joint categories to the actual joint axis direction.

    .. option:: joint_origin_reg (numpy array: float32):

        (N, 3) array of joint origin regression from the anchor points to the actual joint origin.

    .. option:: joint_type (numpy array: float32):

        same as the :ref:`motion_types`.

    .. option:: joint_all_directions (numpy array: float32):

        (14, 3) array represents the 14 joint axis categories.

    .. option:: gt_joints (numpy array: float32):

        (K, 7) array represents the motions of the articulated object. Each row is composed with `[joint_origin, joint_axis, joint_type]`.

    .. option:: gt_proposals (numpy array: float32):

        (K+1, N) array represents the part segmentations of the object. K is the number of movable parts, N is the number of points.

    .. option:: simmat (numpy array: float32):

        A 4096x4096 similarity matrix, where each row represents a part segmentation. Where ith row encodes the part mask that contains the ith point in the object point cloud.

    .. option:: point_idx (numpy array: float32):

        The indices of the selected points during FPS down-sample in the original object point cloud.


