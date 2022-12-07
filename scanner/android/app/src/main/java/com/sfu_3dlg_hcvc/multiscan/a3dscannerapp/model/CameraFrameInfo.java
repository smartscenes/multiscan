package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.model;

import android.util.Log;

import com.google.ar.core.Camera;
import com.google.ar.core.Frame;
import com.google.ar.core.ImageMetadata;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.Arrays;

/**
 * Retrieve camera info such as camera intrinsics and camera pose and translate them in to one json object
 */
public class CameraFrameInfo {
    private static final String TAG = "MultiCamera";
    public long timestamp;
    public long exposureDuration;
    public float[] eulerAngles;
    public float[] intrinsics;
    public float[] rotationQuaternion;
    public float[] rotationQuaternion_from_cameraGetPose;
    public float[] transformMatrices = new float[16];
    public float[] transformMatrices_from_cameraGetPose = new float[16];

    void setSensorExposureTime(Frame frame) {
        try {
            ImageMetadata metadata = frame.getImageMetadata();
            exposureDuration = metadata.getLong(ImageMetadata.SENSOR_EXPOSURE_TIME);
        } catch (Exception e) {
            Log.d(TAG, "Error getting exposure time");
        }
    }

    public CameraFrameInfo(Frame frame, Camera camera) {
        timestamp = frame.getTimestamp();
        setSensorExposureTime(frame);

        //TODO: Need to decide which one to use
        camera.getPose().toMatrix(transformMatrices_from_cameraGetPose, 0);
        rotationQuaternion_from_cameraGetPose = camera.getPose().getRotationQuaternion();
        frame.getAndroidSensorPose().toMatrix(transformMatrices, 0);
        rotationQuaternion = frame.getAndroidSensorPose().getRotationQuaternion();
        float[] focalLength = camera.getImageIntrinsics().getFocalLength();
        float[] principalPoint = camera.getImageIntrinsics().getPrincipalPoint();

        intrinsics = new float[]{
                focalLength[0], 0, 0,
                0, focalLength[1], 0,
                principalPoint[0], principalPoint[1], 1,
        };

        //TODO: Calculate euler angles
        float[] test = new float[16];
        frame.getAndroidSensorPose().extractRotation().toMatrix(test, 0);
    }

    public String toJSONString() throws JSONException {
        JSONObject root = new JSONObject();
        root.put("timestamp", timestamp);
        root.put("exposure_duration", exposureDuration);
//        root.put("euler_angles", convertToJSONArray(eulerAngles));
        root.put("euler_angles", Arrays.toString(eulerAngles));
        root.put("intrinsics", convertToJSONArray(intrinsics));
        root.put("transform", convertToJSONArray(transformMatrices_from_cameraGetPose));
        root.put("transformMatrices_from_androidSensorPose", convertToJSONArray(transformMatrices));
        root.put("rotationQuaternion", convertToJSONArray(rotationQuaternion_from_cameraGetPose));
        root.put("rotationQuaternion_from_androidSensorPose", convertToJSONArray(rotationQuaternion));

        return root.toString();
    }

    private JSONArray convertToJSONArray (float[] floats) throws JSONException {
        JSONArray jsonArray = new JSONArray();
        for (float num : floats) {
            jsonArray.put(num);
        }

        return jsonArray;
    }
}
