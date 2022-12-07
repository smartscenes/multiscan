Acquired Data from Scanner App
==============================

The acquired data from the iOS/Android devices are stored as 5 files:

* Metadata
* RGB stream
* Depth stream
* Depth confidence stream
* Camera parameters

.. _scan_metadata:

Metadata
--------
The metadata includes the meta information of the data collection. Following is an example MultiScan metadata file `scene_00000_00.json` and the description of the attributes in the metadata json file.

.. code-block:: json

    {
        "scene" : {
            "type" : "Kitchen",
            "description" : "Room728-21-1"
        },
        "camera_orientation_euler_angles_format" : "xyz",
        "depth_confidence_avaliable" : true,
        "depth_unit" : "m",
        "depth_confidence_value_range" : [0, 2],
        "camera_orientation_quaternion_format" : "wxyz",
        "number_of_files" : 5,
        "streams" : [
            {
            "frequency" : 60,
            "number_of_frames" : 5763,
            "id" : "color_back_1",
            "file_extension" : "mp4",
            "type" : "color_camera",
            "resolution" : [1440, 1920],
            "encoding" : "h264"
            },
            {
            "frequency" : 60,
            "number_of_frames" : 5763,
            "id" : "depth_back_1",
            "file_extension" : "depth.zlib",
            "type" : "lidar_sensor",
            "resolution" : [192, 256],
            "encoding" : "float16_zlib"
            },
            {
            "id" : "confidence_map",
            "encoding" : "uint8_zlib",
            "number_of_frames" : 5763,
            "type" : "confidence_map",
            "frequency" : 60,
            "file_extension" : "confidence.zlib"
            },
            {
            "id" : "camera_info_color_back_1",
            "encoding" : "jsonl",
            "number_of_frames" : 5763,
            "type" : "camera_info",
            "frequency" : 60,
            "file_extension" : "jsonl"
            }
        ],
    }

.. _scene_type:

.. option:: scene.type (string)
    
    The scene category selected by users on the scanner app during the data collection. Default list of the scene categories: `[Apartment, Bathroom, Bedroom / Hotel, Bookstore / Library, Classroom, Closet, ComputerCluster, Conference Room, Copy Room, Copy/Mail Room, Dining Room, Game room, Gym, Hallway, Kitchen, Laundromat, Laundry Room, Living room / Lounge, Lobby, Mailboxes, Misc., Office, Stairs, Storage/Basement/Garage]`

.. _scene_description:

.. option:: scene.description (string)

    A short descriptive sentence of the scan typed by the user on the scanner app during the data collection.

.. _camera_orientation_euler_angles_format:

.. option:: camera_orientation_euler_angles_format (string)

    The rotation order for the euler angles stored in the camera parameters ``.jsonl`` file with attribute name `euler_angles`. The default rotation order is ``xyz``.

.. _camera_orientation_quaternion_format:

.. option:: camera_orientation_quaternion_format:

    The format of the quaternion vector stored in the camera parameters ``.jsonl`` file with attribute name `quaternion`. The format used in MultiScan is ``wxyz``, this field is used to differentiate the other quaternion format ``xyzw``.

.. _depth_confidence_avaliable:

.. option:: depth_confidence_avaliable (bool):

    A boolean variable indicate whether the depth confidence file is available for the scan.

.. _depth_unit:

.. option:: depth_unit (string):

    The unit of the pixel values in the depth maps compressed in the depth stream ``.depth.zlib`` file. The unit can be ``m`` (meter) or ``mm`` (millimeter).

.. _depth_confidence_value_range:

.. option:: _depth_confidence_value_range (list: uint):

    The range of the pixel values in the depth confidence map compressed in the confidence stream ``.confidence.zlib`` file. The range is a closed interval, represented by a list of 2 unsigned integers `[min, max]`.

.. _number_of_files:

.. option:: number_of_files (uint):

    The number of files generated during the data acquisition by scanner app. When uploading the data to the processing server compares the number of files received with matched md5 hash on the server and this attribute to determine if the upload is complete and successful.

.. _streams:

.. option:: streams (list: dict):

    A list of the metadata of the stream files. By default, there are 4 elements in the list with the following order: 1. RGB stream metadata, 2. depth stream metadata, 3. depth confidence stream metadata 4. camera parameters stream metadata.

.. _streams_frequency:

.. option:: streams.frequency (uint):

    The frame rate of the collected stream in unit ``fps``

.. _streams_number_of_frames:

.. option:: streams.number_of_frames (uint):

    The total number of frames acquired in the data stream.

.. _streams_id:

.. option:: streams.id (string):

    The ID of the stream metadata, used to identify the metadata in the `streams` list. ``back_1`` in the ID indicate the stream is captured with the camera 1 at the back of the device.

.. _streams_file_extension:

.. option:: streams.file_extension (string):

    The file extension of the corresponding stream file.

.. _streams_type:

.. option:: streams.type (string):

    A string for indicate the type of the stream metadata.

.. _streams_resolution:

.. option:: streams.resolution (list: uint):

    The resolution of the frame encoded in the stream file. The list has 2 elements `[height, width]` in the unit of pixels.

.. _streams_encoding:

.. option:: streams.encoding (string):

    The encoding method used to encode the acquired frames to the stream file.


.. _rgb_stream:

RGB stream
----------

Recorded RGB frames is encoded with H.264 codec, stored in the `scene_xxxxx_xx.mp4` file. The frame rate, number of frames, and frame resolution can be found in the :ref:`metadata <scan_metadata>`.

.. todo::

    Add code block for how to decode .mp4 file to .png RGB frames

.. _depth_stream:

Depth stream
------------

The iOS version of the scanner app records depth as 16-bit float values in meters, the Android version records depth as 16-bit unsigned int values in millimetres. The raw depth frames are stream compressed using zlib compression. The frame rate, number of frames, and frame resolution can be found in the :ref:`metadata <scan_metadata>`.

.. todo::

    Add code block for how to decode .depth.zlib file to .png depth maps

.. _depth_confidence_stream:

Depth confidence stream
-----------------------

Confidence map pixels are 8-bit unsigned integers. The iOS version of the scanner app has the range of the confidence values `[0, 2]`, with the mapping `0: low, 1: medium, 2: high` to the original `ARKit ARConfidenceLevel`_. The range of the confidence values with the Android version is `[0, 255]`, the larger confidence value represents the higher confidence in the depth value, more details available at `ARCore acquireRawDepthConfidenceImage`_. The raw confidence maps are stream compressed using zlib compression. The frame rate, number of frames, and frame resolution can be found in the :ref:`metadata <scan_metadata>`.

.. todo::

    Add code block for how to decode .confidence.zlib file to .png confidence maps

Camera parameters
-----------------
Camera parameters are stored in `JSON Lines`_ format, with each line as a JSON data stores the camera parameters for each frame. Each camera has following parameters: `intrinsics`, `transform`, `euler_angles`, `quaternion`, `timestamp`, `exposure_duration`.

intrinsics
    A 9x1 vector corresponds to the column major 3x3 intrinsics matrix for the RGB frames in :ref:`rgb_stream`. The intrinsic matrix for depth frames can be obtained by scaling the `intrinsics` like `code intrinsic scaling`_.

transform
    A 16x1 vector corresponds to the column major 4x4 6 DoF camera pose matrix, which denotes the transformation from camera coordinates to 3D world coordinates. According to `ARKit transform`_, the x-axis points from the front-facing camera toward the Home button. The y-axis points upward, and the z-axis points away from the device on the screen side.

    To convert it back into the 4x4 camera pose transformation matrix:

    .. code-block:: python
        :linenos:

        import json
        import numpy as np
        cam_params = json.loads('one line in the scene_xxxxx_xx.jsonl')
        transform = np.asarray(cam_params.get('transform'))
        transform = np.reshape(transform, (4, 4), order='F')

    To convert the camera coordinates from ARKit camera coordinates to Open3D camera coordinates:

    .. code-block:: python
        :linenos:

        transform = np.dot(transform, np.diag([1, -1, -1, 1]))
        transform = transform / transform[3][3]

    .. note::
        The camera pose 4x4 transformation matrix is not the camera extrinsics. Inverse the calculated 4x4 matrix, to convert it into camera extrinsics.

euler_angles
    A 3x1 float vector express the camera orientation in roll, pitch, yaw values which denotes the transformation from camera coordinates to 3D world coordinates. The order is described in :ref:`camera_orientation_euler_angles_format`.

quaternion
    A 4x1 float quaternion vector denotes the transformation from camera coordinates to 3D world coordinates. The order is described in :ref:`camera_orientation_quaternion_format`. By default, the order is ``wxyz``.

timestamp
    An integer value indicates the time the frame was captured. See more details at `ARKit timestamp`_

exposure_duration
    An integer value indicates the duration of the camera exposure, effects the motion blur. See more details at `ARKit exposureDuration`_.

.. _ARKit ARConfidenceLevel: https://developer.apple.com/documentation/arkit/arconfidencelevel
.. _ARKit timestamp: https://developer.apple.com/documentation/arkit/arframe/2867973-timestamp
.. _ARKit exposureDuration: https://developer.apple.com/documentation/arkit/arcamera/3182986-exposureduration
.. _ARKit transform: https://developer.apple.com/documentation/arkit/arcamera/2866108-transform
.. _ARCore acquireRawDepthConfidenceImage: https://developers.google.com/ar/reference/java/com/google/ar/core/Frame#acquireRawDepthConfidenceImage-

.. _code intrinsic scaling: https://github.com/smartscenes/multiscan/blob/a050c47a81dd9227e6f27823b07e2204b656fc2a/reconstruction/scripts/bridge.py#L215

.. _JSON Lines: https://jsonlines.org/
