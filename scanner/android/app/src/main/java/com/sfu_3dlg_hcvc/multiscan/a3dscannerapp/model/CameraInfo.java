package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.model;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Data class that hold all the information about the recorded scene and convert them into a json object
 */
public class CameraInfo {
    public int depthImageWidth;
    public int depthImageHeight;
    public String deviceName = "";
    public String userName = "";
    public int[] imageDimensions;
    public int[] depthConfidenceValueRange;
    public String frameCount = "";
    public String sceneType = "";
    public String description = "";
    public String manufacturer = "";
    public String modelNumber = "";
    public String quaternionFormat = "";
    public String depthUnit = "";
    public double[] GPS;
    public boolean confidenceAvailable = false;
    public String depthConfidenceImageType = "";
    public int numberFiles = 5;

    public String toJSONString() throws JSONException {
        JSONArray list = new JSONArray();
        list.put(formRGBCameraInfo());
        list.put(formDepthCameraInfo());
        list.put(formConfidenceDataInfo());
        list.put(formRGBDataInfo());
        JSONObject root = new JSONObject();
        root.put("device", formDeviceInfo());
        root.put("scene", formSceneInfo());
        root.put("user", formUserInfo());
        root.put("streams", list);
        root.put("number_of_files", numberFiles);
        root.put("depth_unit", depthUnit);
        root.put("depth_confidence_available", confidenceAvailable);
        root.put("camera_orientation_quaternion_format", quaternionFormat);
        root.put("depth_confidence_value_range", convertToJSONArray(depthConfidenceValueRange));
        root.put("camera_orientation_quaternion_format", quaternionFormat);
        root.put("camera_orientation_euler_angles_format", JSONObject.NULL);
        return root.toString();
    }

    private JSONObject formRGBCameraInfo() throws JSONException{
        JSONObject root = new JSONObject();
        root.put("extrinsics", JSONObject.NULL);
        root.put("frequency", 60);
        root.put("number_of_frames", Integer.parseInt(frameCount));
        root.put("id", "color_back_1");
        root.put("file_extension", "mp4");
        root.put("intrinsics", JSONObject.NULL);
        root.put("type", "rgb_camera");
        root.put("resolution", convertToJSONArray(imageDimensions));
        root.put("encoding", "h264");

        return root;
    }

    private JSONObject formDepthCameraInfo() throws JSONException{
        JSONObject root = new JSONObject();
        root.put("extrinsics", JSONObject.NULL);
        root.put("frequency", 60);
        root.put("number_of_frames", Integer.parseInt(frameCount));
        root.put("id", "depth_back_1");
        root.put("file_extension", "depth.zlib");
        root.put("intrinsics", JSONObject.NULL);
        root.put("type", "ARCore");
        root.put("resolution", convertToJSONArray(new int[]{depthImageHeight, depthImageWidth}));
        root.put("encoding", "uint8_zlib");
        return root;
    }

    private JSONObject formConfidenceDataInfo() throws JSONException{
        JSONObject root = new JSONObject();
        root.put("frequency", 60);
        root.put("number_of_frames", Integer.parseInt(frameCount));
        root.put("id", "confidence_map");
        root.put("file_extension", "confidence.zlib");
        root.put("type", "confidence_map");
        root.put("encoding", "uint8_zlib");

        return root;
    }

    private JSONObject formRGBDataInfo() throws JSONException{
        JSONObject root = new JSONObject();
        root.put("frequency", 60);
        root.put("number_of_frames", Integer.parseInt(frameCount));
        root.put("id", "camera_info_color_back_1");
        root.put("file_extension", "jsonl");
        root.put("type", "camera_info");
        root.put("encoding", "jsonl");

        return root;
    }

    private JSONObject formDeviceInfo() throws JSONException{
        JSONObject root = new JSONObject();
        root.put("name", deviceName);
        root.put("id", JSONObject.NULL);
        root.put("type", manufacturer + "_" + modelNumber);

        return root;
    }

    private JSONObject formSceneInfo() throws JSONException{
        JSONObject root = new JSONObject();
        root.put("gps_location", convertToJSONArray(GPS));
        root.put("description", description);
        root.put("type", sceneType);

        return root;
    }

    private JSONObject formUserInfo() throws JSONException{
        JSONObject root = new JSONObject();
        root.put("name", userName);
        return root;
    }



    private JSONArray convertToJSONArray (int[] ints) {
        JSONArray jsonArray = new JSONArray();
        for (int num : ints) {
            jsonArray.put(num);
        }

        return jsonArray;
    }

    private JSONArray convertToJSONArray (float[] floats) throws JSONException{
        JSONArray jsonArray = new JSONArray();
        for (float num : floats) {
            jsonArray.put(num);
        }

        return jsonArray;
    }

    private JSONArray convertToJSONArray (double[] floats) throws JSONException{
        JSONArray jsonArray = new JSONArray();
        for (double num : floats) {
            jsonArray.put(num);
        }

        return jsonArray;
    }
}
