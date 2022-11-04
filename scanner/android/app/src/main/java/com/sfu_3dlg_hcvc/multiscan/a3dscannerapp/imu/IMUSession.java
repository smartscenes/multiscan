package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.imu;

import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Build;
import android.util.Log;

import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.VideoCaptureActivity;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.fio.FileStreamer;

import java.io.IOException;
import java.security.KeyException;
import java.util.HashMap;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * An IMUSession class that is used to retrieve sensor information
 */
public class IMUSession implements SensorEventListener {
    private static final String LOG_TAG = IMUSession.class.getSimpleName();

    private VideoCaptureActivity mContext;
    private HashMap<String, Sensor> mSensors = new HashMap<>();
    private SensorManager mSensorManager;
    private float mInitialStepCount = -1;
    public FileStreamer mFileStreamer = null;

    public AtomicBoolean mIsRecording = new AtomicBoolean(false);
    private AtomicBoolean mIsWritingFile = new AtomicBoolean(false);


    public HashMap<String, Integer> mSensorCounter = new HashMap<>();

    public static final int mFrequency = 100;

    private float[] mAcceBias = new float[3];

    public String[] ids = {"gyro", "acce", "gravity", "magnet", "orientation"};
    public HashMap<String, String> shortNames = new HashMap<>();
    public HashMap<String, String> fullNames = new HashMap<>();

    /**
     * Each sensor has a specific file writer under file streamer instance.
     * When the sensor updates, the file writer will write the records in to specific file.
     * @param context Activity Context
     */
    public IMUSession(VideoCaptureActivity context){
        mContext = context;
        mSensorManager = (SensorManager)mContext.getSystemService(Context.SENSOR_SERVICE);

        mSensors.put("gyro", mSensorManager.getDefaultSensor(Sensor.TYPE_GYROSCOPE));
        // Some phones (e.g. Pixel 2XL) automatically calibration accelerometer bias. For unified
        // processing framework, we use uncalibration acceleroemter and provide external calibration.
        if(Build.VERSION.SDK_INT < 26){
            Log.i(LOG_TAG, String.format(Locale.US, "API level: %d, Accelermeter used.", Build.VERSION.SDK_INT));
            mSensors.put("acce", mSensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER));
        } else {
            Log.i(LOG_TAG, String.format(Locale.US, "API level: %d, Accelermeter_uncalibrated used.", Build.VERSION.SDK_INT));
            mSensors.put("acce", mSensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER_UNCALIBRATED));
        }
        
        mSensors.put("gravity", mSensorManager.getDefaultSensor(Sensor.TYPE_GRAVITY));
        mSensors.put("magnet", mSensorManager.getDefaultSensor(Sensor.TYPE_MAGNETIC_FIELD));
        mSensors.put("orientation", mSensorManager.getDefaultSensor(Sensor.TYPE_ORIENTATION));
        registerSensors();

        shortNames.put("gyro", "rot");
        shortNames.put("acce", "acce");
        shortNames.put("gravity", "grav");
        shortNames.put("magnet", "mag");
        shortNames.put("orientation", "atti");

        fullNames.put("gyro", "rotation");
        fullNames.put("acce", "accelerometer");
        fullNames.put("gravity", "gravity");
        fullNames.put("magnet", "magnet");
        fullNames.put("orientation", "attitude");
    }

    public void registerSensors(){
        for(Sensor s: mSensors.values()){
//            mSensorManager.registerListener(this, s, SensorManager.SENSOR_DELAY_FASTEST);
            mSensorManager.registerListener(this, s, mFrequency);
        }
    }

    public void unregisterSensors(){
        for(Sensor s: mSensors.values()){
            mSensorManager.unregisterListener(this, s);
        }
    }
    public boolean isRecording(){
        return mIsRecording.get();
    }

    public void startSession(String streamFolder, final String scanFolderName){
        if (streamFolder != null){
            mFileStreamer = new FileStreamer(mContext, streamFolder);
            mSensorCounter.clear();
            try {
                for(String id:ids) {
                    mFileStreamer.addFile(id, scanFolderName + "." + shortNames.get(id), true);
                    mFileStreamer.addFile(id + "_ascii", scanFolderName + "." + shortNames.get(id) + "_ascii", true);
                    mSensorCounter.put(id, 0);
                    mSensorCounter.put(id + "_ascii", 0);
                }

                mIsWritingFile.set(true);

            } catch (IOException e){
                mContext.showToast("Error occurs when creating output IMU files.");
                e.printStackTrace();
            }

        }
        mIsRecording.set(true);
    }

    public void stopSession(){
        mIsRecording.set(false);

        if(mIsWritingFile.get()){

            mIsWritingFile.set(false);
            try {
                mFileStreamer.endFiles();
            } catch (IOException e){
                e.printStackTrace();
            }
//            mFileStreamer = null;
        }

        mInitialStepCount = -1;
    }

    public void resetSession() {
        mFileStreamer = null;
    }

    @Override
    public void onSensorChanged(final SensorEvent event){
        long timestamp = event.timestamp;
        float[] values = {0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f};
//        Log.i("imuSession", String.format("mIsRecording:%b, mIsWritingFile:%b", mIsRecording.get(), mIsWritingFile.get()));
        try {
            switch (event.sensor.getType()) {
                case Sensor.TYPE_ACCELEROMETER:
                    if (mIsRecording.get() && mIsWritingFile.get()) {
                        mFileStreamer.addRecord(timestamp, "acce", 3, event.values, "byte");
                        mFileStreamer.addRecord(timestamp, "acce_ascii", 3, event.values, "raw");
                        mSensorCounter.put("acce", mSensorCounter.get("acce") + 1);
                        mSensorCounter.put("acce_ascii", mSensorCounter.get("acce_ascii") + 1);

                    }
                    break;

                case Sensor.TYPE_GYROSCOPE:
                    if (mIsRecording.get() && mIsWritingFile.get()) {
//                        Log.i("imuSession", String.format("record gyro data %s", event.values.toString()));
                        mFileStreamer.addRecord(timestamp, "gyro", 3, event.values, "byte");
                        mFileStreamer.addRecord(timestamp, "gyro_ascii", 3, event.values, "raw");
                        mSensorCounter.put("gyro", mSensorCounter.get("gyro") + 1);
                        mSensorCounter.put("gyro_ascii", mSensorCounter.get("gyro_ascii") + 1);
                    }
                    break;

                case Sensor.TYPE_GRAVITY:
                    if (mIsRecording.get() && mIsWritingFile.get()) {
                        mFileStreamer.addRecord(timestamp, "gravity", 3, event.values, "byte");
                        mFileStreamer.addRecord(timestamp, "gravity_ascii", 3, event.values, "raw");

                        mSensorCounter.put("gravity", mSensorCounter.get("gravity") + 1);
                        mSensorCounter.put("gravity_ascii", mSensorCounter.get("gravity_ascii") + 1);
                    }
                    break;

                case Sensor.TYPE_ORIENTATION:
                    if (mIsRecording.get() && mIsWritingFile.get()) {
                        mFileStreamer.addRecord(timestamp, "orientation", 3, event.values, "byte");
                        mFileStreamer.addRecord(timestamp, "orientation_ascii", 3, event.values, "raw");
                        mSensorCounter.put("orientation", mSensorCounter.get("orientation") + 1);
                        mSensorCounter.put("orientation_ascii", mSensorCounter.get("orientation_ascii") + 1);

                    }
                    break;

                case Sensor.TYPE_MAGNETIC_FIELD:
                    if (mIsRecording.get() && mIsWritingFile.get()) {
                        mFileStreamer.addRecord(timestamp, "magnet", 3, event.values, "byte");
                        mFileStreamer.addRecord(timestamp, "magnet_ascii", 3, event.values, "raw");
                        mSensorCounter.put("magnet", mSensorCounter.get("magnet") + 1);
                        mSensorCounter.put("magnet_ascii", mSensorCounter.get("magnet_ascii") + 1);

                    }
                    break;

                case Sensor.TYPE_ACCELEROMETER_UNCALIBRATED:
                    mAcceBias[0] = event.values[3];
                    mAcceBias[1] = event.values[4];
                    mAcceBias[2] = event.values[5];
                    if (mIsRecording.get() && mIsWritingFile.get()) {
                        mFileStreamer.addRecord(timestamp, "acce", 3, event.values, "byte");
                        mFileStreamer.addRecord(timestamp, "acce_ascii", 3, event.values, "raw");
                        mSensorCounter.put("acce", mSensorCounter.get("acce") + 1);
                        mSensorCounter.put("acce_ascii", mSensorCounter.get("acce_ascii") + 1);
                    }
                    break;
            }
        } catch (IOException | KeyException e){
            e.printStackTrace();
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy){

    }
}
