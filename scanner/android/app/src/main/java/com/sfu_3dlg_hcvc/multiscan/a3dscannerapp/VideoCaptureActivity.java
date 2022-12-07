package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp;

import android.Manifest;
import android.app.AlertDialog;
import android.content.ContentResolver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.graphics.SurfaceTexture;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCaptureSession;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraDevice;
import android.hardware.camera2.CameraManager;
import android.hardware.camera2.CaptureRequest;
import android.hardware.camera2.params.StreamConfigurationMap;
import android.location.Location;
import android.location.LocationManager;
import android.media.MediaMetadataRetriever;
import android.media.MediaRecorder;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.HandlerThread;
import android.provider.MediaStore;
import android.provider.Settings;
import android.util.Log;
import android.util.Size;
import android.util.SparseIntArray;
import android.view.Surface;
import android.view.TextureView;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;
import androidx.preference.PreferenceManager;

import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.imu.IMUSession;

import org.json.simple.JSONArray;
import org.json.simple.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.Writer;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;

/**
 * The videoCapture page including a camera preview and a record button.
 * It will ask write permission if not before. Once the button is clicked,
 * users are asked to give a type and description about the record.
 * After that, the camera record and imu session starts.
 */
public class VideoCaptureActivity extends AppCompatActivity {

    private static final String TAG = "scanAppActivity";
    private static int VIDEO_REQUEST = 101;

    private TextureView mTextureView;
    private ImageButton mRecordImageButton;
    private boolean mIsRecording = false;

    private IMUSession mIMUSession;
    private String mDescription;
    private String mSceneType;

    private static final int REQUEST_CAMERA_PERMISSION_RESULT = 0;
    private static final int REQUEST_WRITE_EXTERNAL_STORAGE_PERMISSION_RESULT = 1;
    private static final int REQUEST_ACCESS_FINE_LOCATION_PERMISSION_RESULT = 2;
    // FIXME: extend it for multiple cameras
    private String mCameraId;
    private float[] mCameraLensIntrinsic;
    // FIXME: what is mPreviewSize for
    private Size mPreviewSize;
    private Size mVideoSize;
    private MediaRecorder mMediaRecorder;
    private CaptureRequest.Builder mCaptureRequestBuilder;

    private int mTotalRotation;
    private int mBitRate = 15000000;
    private int mFrameRate = 60;

    private File mAppFilesFolder;
    private String mAppFilesFolderName = MainActivity.appFilesFolderName;
    private String mScanFolderName;
    private File mScanFolder;
    private String mVideoFilePath;
    private String mMetaDataFileName;


    private static SparseIntArray ORIENTATIONS = new SparseIntArray();
    static {
        ORIENTATIONS.append(Surface.ROTATION_0, 0);
        ORIENTATIONS.append(Surface.ROTATION_90, 90);
        ORIENTATIONS.append(Surface.ROTATION_180, 180);
        ORIENTATIONS.append(Surface.ROTATION_270, 270);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_video_capture);

        createAppFilesFolder();

        mMediaRecorder = new MediaRecorder();
        mTextureView = (TextureView) findViewById(R.id.textureView);
        mRecordImageButton = (ImageButton) findViewById(R.id.videoOnlineImageButton);
        mRecordImageButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if(mIsRecording) {
                    mIsRecording = false;
                    mRecordImageButton.setImageResource(R.mipmap.btn_video_online_foreground);
                    mMediaRecorder.stop();
                    mMediaRecorder.reset();
                    mIMUSession.stopSession();

//                    AsyncTask.execute(new Runnable() {
//                        @Override
//                        public void run() {
//                            saveMetaData();
//                        }
//                    });

                    // store video data
                    Intent mediaStoreUpdateIntent = new Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE);
                    mediaStoreUpdateIntent.setData(Uri.fromFile(new File(mVideoFilePath)));
                    sendBroadcast(mediaStoreUpdateIntent);

                    startPreview();
                    saveMetaData();
                    mIMUSession.resetSession();
                } else {
                    try {
                        if (checkWriteStoragePermission()) {

                            askForInputAndStartRecord();
                        }
                    } catch (IOException e) {
                        e.printStackTrace();
                    }

                }
            }
        });

        mIMUSession = new IMUSession(this);
    }


    private TextureView.SurfaceTextureListener mSurfaceTextureListener = new TextureView.SurfaceTextureListener() {
        @Override
        public void onSurfaceTextureAvailable(SurfaceTexture surface, int width, int height) {
            showToast("Texture view is available");
            setupCamera(width, height);
            connectCamera();
        }

        @Override
        public void onSurfaceTextureSizeChanged(SurfaceTexture surface, int width, int height) {

        }

        @Override
        public boolean onSurfaceTextureDestroyed(SurfaceTexture surface) {
            return false;
        }

        @Override
        public void onSurfaceTextureUpdated(SurfaceTexture surface) {

        }
    };

    private CameraDevice mCameraDevice;
    // FIXME: what is the difference between camera
    private CameraDevice.StateCallback mCameraDeviceStateCallback = new CameraDevice.StateCallback() {
        @Override
        public void onOpened(@NonNull CameraDevice camera) {
            mCameraDevice = camera;
            showToast("Camera connection Made!");

            if(!mIsRecording) {
                startPreview();
            }
        }

        @Override
        public void onDisconnected(@NonNull CameraDevice camera) {
            showToast("Camera close!");
            closeCamera();
        }

        @Override
        public void onError(@NonNull CameraDevice camera, int error) {
            showToast("Camera close with Error!");
            closeCamera();
        }
    };

    private void startPreview() {
        SurfaceTexture surfaceTexture = mTextureView.getSurfaceTexture();
        surfaceTexture.setDefaultBufferSize(mPreviewSize.getWidth(), mPreviewSize.getHeight());
        Surface previewSurface = new Surface(surfaceTexture);

        try {
            mCaptureRequestBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_PREVIEW);
            mCaptureRequestBuilder.addTarget(previewSurface);

            mCameraDevice.createCaptureSession(Arrays.asList(previewSurface),
                    new CameraCaptureSession.StateCallback() {
                        // FIXME: what is NonNull?
                        // FIXME: Is the session always running, shall we stop the session?
                        @Override
                        public void onConfigured(@NonNull CameraCaptureSession session) {
                            try {
                                session.setRepeatingRequest(mCaptureRequestBuilder.build(),
                                        null, mBackgroundHandler);
                            } catch (CameraAccessException e) {
                                e.printStackTrace();
                            }
                        }

                        @Override
                        public void onConfigureFailed(@NonNull CameraCaptureSession session) {
                            showToast("Unable to setup camera preview");
                        }
                    }, null);
        } catch (CameraAccessException e) {
            e.printStackTrace();
        }
    }


    class PromptRunnable implements Runnable {
        public void run() {
            this.run();
        }
    }

    void promptForResult(final PromptRunnable postrun) {
        mDescription = "";
        mSceneType = "";

        final AlertDialog.Builder desBuilder = new AlertDialog.Builder(this);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.MATCH_PARENT);
        final EditText input = new EditText(VideoCaptureActivity.this);
        input.setLayoutParams(lp);
        desBuilder.setTitle("Add description")
                .setView(input);
        desBuilder.create();
        desBuilder.setPositiveButton("DONE", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialogInterface, int i) {
                mDescription = input.getText().toString();
                Toast.makeText(getApplicationContext(), "SceneType:" + mSceneType, Toast.LENGTH_SHORT).show();
                postrun.run();
            }
        });

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Select ScenceType");
        final String[] sceneTypes = getResources().getStringArray(R.array.sceneType);
        builder.setSingleChoiceItems((CharSequence[])sceneTypes, -1, new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                mSceneType = sceneTypes[which];
                dialog.dismiss();
                desBuilder.show();
            }
        });

        builder.show();
    }

    private void askForInputAndStartRecord() {
        promptForResult(new PromptRunnable(){
            public void run() {
                if(!mDescription.equals("") && !mSceneType.equals("")) {
                    mIsRecording = true;
                    mRecordImageButton.setImageResource(R.mipmap.btn_video_offline_foreground);
                    startRecord();
                    mMediaRecorder.start();
                }
                else {
                    Toast.makeText(getApplicationContext(),
                            "Please select sceneType and input your description",
                            Toast.LENGTH_SHORT).show();
                }
            }
        });
    }

    private void saveMetaData() {
        JSONObject root = new JSONObject();

        SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(VideoCaptureActivity.this);
        JSONObject device = new JSONObject();
        device.put("id", Settings.Secure.getString(VideoCaptureActivity.this.getContentResolver(),
                Settings.Secure.ANDROID_ID));

        String manufacturer = Build.MANUFACTURER;
        String model = Build.MODEL;
        if (!model.toLowerCase().startsWith(manufacturer.toLowerCase())) {
            device.put("type", manufacturer + " " + model);
        } else {
            device.put("type", model);
        }

        device.put("name", preferences.getString("device_name", ""));
        root.put("device", device);

        JSONObject user = new JSONObject();
        user.put("name", preferences.getString("user_name", ""));
        root.put("user", user);

        JSONObject scene = new JSONObject();
        scene.put("description", mDescription);
        scene.put("sceneType", mSceneType);

        LocationManager locationManager = (LocationManager)
                getSystemService(Context.LOCATION_SERVICE);
        try {
            if(checkLocationPermission()){
                Location locationGPS = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
                if (locationGPS != null) {
                    scene.put("gps",  new ArrayList<>(Arrays.asList(locationGPS.getLatitude(), locationGPS.getLongitude())));
                }
                else {
                    scene.put("gps", null);
                }
            }
            else {
                scene.put("gps", null);
            }
        }
        catch (SecurityException e) {
            scene.put("gps", null);
            e.printStackTrace();
        }
        root.put("scene", scene);

        JSONArray sensors = new JSONArray();
        //get origin video info
        JSONObject sensor_camera = new JSONObject();
        MediaMetadataRetriever retriever = new MediaMetadataRetriever();
        retriever.setDataSource(mVideoFilePath);
        String videoWidth = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_WIDTH);
        String videoHeight = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_HEIGHT);
        String rotation = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_ROTATION);
        String frameCount = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_FRAME_COUNT);
        String frameRate = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_CAPTURE_FRAMERATE);
        long duration = Long.valueOf(retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)) * 1000;
        sensor_camera.put("id", "color_back_1");
        sensor_camera.put("type", "color_camera");
        sensor_camera.put("resolution", new ArrayList<>(Arrays.asList(videoWidth, videoHeight)));

        if (mCameraLensIntrinsic != null) {
            sensor_camera.put("focal_length", new ArrayList<>(Arrays.asList(mCameraLensIntrinsic[0], mCameraLensIntrinsic[1])));
            sensor_camera.put("principle_point", new ArrayList<>(Arrays.asList(mCameraLensIntrinsic[2], mCameraLensIntrinsic[3])));
        }
        else {
            sensor_camera.put("focal_length", null);
            sensor_camera.put("principle_point", null);
        }
        sensor_camera.put("extrinsics_matrix", null);
        sensor_camera.put("encoding", "h264");
        sensor_camera.put("num_frames", frameCount);
        sensor_camera.put("frequency", mFrameRate);
        sensors.add(sensor_camera);

        for (String id : mIMUSession.ids) {
            JSONObject imu = new JSONObject();
            imu.put("num_frames", mIMUSession.mSensorCounter.get(id));
            imu.put("freqeuncy", mIMUSession.mFrequency);
            imu.put("id", mIMUSession.shortNames.get(id)+"_1");
            imu.put("type", mIMUSession.fullNames.get(id)+"_1");
            sensors.add(imu);
            String[] suffixes = {"", "_ascii"};
            for (String suffix:suffixes){
                String name = id + suffix;
                // add header
                File originFile = mIMUSession.mFileStreamer.getFile(name);

                if(!preferences.getBoolean("debug_flag", false) && suffix.equals("_ascii")) {
                    originFile.delete();
                    originFile = null;
                }

                if(originFile == null) {
                    continue;
                }


                String originFilePath = originFile.getAbsolutePath();

                String header;
                if (suffix.equals("_ascii")) {
                    header = Util.makePlyHeader("imu", mIMUSession.fullNames.get(id), mIMUSession.mSensorCounter.get(name), true);
                } else {
                    header = Util.makePlyHeader("imu", mIMUSession.fullNames.get(id), mIMUSession.mSensorCounter.get(name), false);
                }

                File finalFile = new File(originFilePath + ".temp");

                try {
                    Writer writer = new FileWriter(finalFile.getAbsolutePath());
                    writer.write(header);
                    writer.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }

                try {
                    OutputStream os = new FileOutputStream(finalFile, true);
                    InputStream is = new FileInputStream(originFile);
                    byte[] buffer = new byte[0xFFFF];
                    for (int len = is.read(buffer); len != -1; len = is.read(buffer)) {
                        os.write(buffer, 0, len);
                    }
                    os.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
                // remove the original file
                originFile.delete();
                finalFile.renameTo(new File(originFilePath));
            }

        }
        root.put("stream", sensors);
        //Write JSON file
        try {
            File metaDataFile = new File(mScanFolder, mScanFolderName+".txt");
            FileWriter file = new FileWriter(new File(metaDataFile.getAbsolutePath()));
            file.write(root.toJSONString());
            file.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private void stopRecord() {
    }

    private void startRecord() {
        mIMUSession.startSession(mScanFolder.getAbsolutePath(), mScanFolderName);

        try {
            setupMediaRecorder();
            SurfaceTexture surfaceTexture = mTextureView.getSurfaceTexture();
            surfaceTexture.setDefaultBufferSize(mPreviewSize.getWidth(), mPreviewSize.getHeight());
            Surface previewSurface = new Surface(surfaceTexture);
            // what is recorderSurface, where it shows?
            Surface recorderSurface = mMediaRecorder.getSurface();
            mCaptureRequestBuilder = mCameraDevice.createCaptureRequest(CameraDevice.TEMPLATE_RECORD);
            mCaptureRequestBuilder.addTarget(previewSurface);
            mCaptureRequestBuilder.addTarget(recorderSurface);

            mCameraDevice.createCaptureSession(Arrays.asList(previewSurface, recorderSurface),
                    new CameraCaptureSession.StateCallback() {
                        @Override
                        public void onConfigured(@NonNull CameraCaptureSession session) {
                            try {
                                session.setRepeatingRequest(
                                        mCaptureRequestBuilder.build(), null, null
                                );
                            } catch (CameraAccessException e) {
                                e.printStackTrace();
                            }
                        }

                        @Override
                        public void onConfigureFailed(@NonNull CameraCaptureSession session) {
                            Log.d(TAG, "onConfigureFailed: startRecord");
                        }
                    }, null);
        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    private void closeCamera() {
        if (mCameraDevice != null) {
            mCameraDevice.close();
            mCameraDevice = null;
        }
    }



    @Override
    protected void onResume() {
        super.onResume();

        startBackgroundThread();

        if(mTextureView.isAvailable()){
            setupCamera(mTextureView.getWidth(), mTextureView.getHeight());
            connectCamera();
        } else {
            mTextureView.setSurfaceTextureListener(mSurfaceTextureListener);
        }
    }

    @Override
    protected void onPause() {
        closeCamera();

        stopBackgroundThread();


        super.onPause();
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions,
                                           int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if(requestCode == REQUEST_CAMERA_PERMISSION_RESULT) {
            if (grantResults[0] != PackageManager.PERMISSION_GRANTED) {
                showToast("Application will not run without camera services!");
            }
        }
        if(requestCode == REQUEST_WRITE_EXTERNAL_STORAGE_PERMISSION_RESULT) {
            if (grantResults[0] == PackageManager.PERMISSION_GRANTED) {
//                mIsRecording = true;
//                mRecordImageButton.setImageResource(R.mipmap.btn_video_offline_foreground);
                createAppFilesFolder();
                createVideoFileName();
                showToast("Write external storage permission granted!");
            } else {
                showToast("Application will not run without writing external storage!");
            }
        }
    }

    private void setupCamera(int width, int height) {
        CameraManager cameraManager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        try {
            for(String cameraId : cameraManager.getCameraIdList()){
                CameraCharacteristics cameraCharacteristics = cameraManager.getCameraCharacteristics(cameraId);
                if (cameraCharacteristics.get(CameraCharacteristics.LENS_FACING) ==
                        cameraCharacteristics.LENS_FACING_FRONT) {
                    continue;
                }
                StreamConfigurationMap map = cameraCharacteristics.get(CameraCharacteristics.SCALER_STREAM_CONFIGURATION_MAP);
                int deviceOrientation = getWindowManager().getDefaultDisplay().getRotation();
                mTotalRotation = sensorToDeviceRotation(cameraCharacteristics, deviceOrientation);
                boolean swapRotation = mTotalRotation == 90 || mTotalRotation == 270;
                int rotatedWidth = width;
                int rotatedHeight = height;
                if(swapRotation) {
                    rotatedWidth = height;
                    rotatedHeight = width;
                }
                mPreviewSize = chooseOptimalSize(map.getOutputSizes(SurfaceTexture.class), rotatedWidth, rotatedHeight);
                mVideoSize = chooseOptimalSize(map.getOutputSizes(MediaRecorder.class), rotatedWidth, rotatedHeight);
                mCameraId = cameraId;
                mCameraLensIntrinsic = cameraCharacteristics.get(cameraCharacteristics.LENS_INTRINSIC_CALIBRATION);
                return;
            }
        } catch (CameraAccessException e) {
            e.printStackTrace();
        }
    }

    private void connectCamera() {
        CameraManager cameraManager = (CameraManager)getSystemService(Context.CAMERA_SERVICE);
        try {
            // FIXME: what is this?
            if(Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                if(ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) ==
                        PackageManager.PERMISSION_GRANTED) {
                    cameraManager.openCamera(mCameraId, mCameraDeviceStateCallback, mBackgroundHandler);
                } else {
                    if(shouldShowRequestPermissionRationale(Manifest.permission.CAMERA)) {
                        showToast("Video app required access to camera");
                    }
                    // FIXME: why REQUEST_CAMERA_PERMISSION_RESULT is final?
                    requestPermissions(new String[] {Manifest.permission.CAMERA}, REQUEST_CAMERA_PERMISSION_RESULT);
                }
            } else {
                cameraManager.openCamera(mCameraId, mCameraDeviceStateCallback, mBackgroundHandler);
            }
        } catch (CameraAccessException e) {
            e.printStackTrace();
        }

    }

    /**
     * Gets the corresponding path to a file from the given content:// URI
     * @param selectedVideoUri The content:// URI to find the file path from
     * @param contentResolver The content resolver to use to perform the query.
     * @return the file path as a string
     */
    private String getFilePathFromContentUri(Uri selectedVideoUri,
                                             ContentResolver contentResolver) {
        String filePath;
        String[] filePathColumn = {MediaStore.MediaColumns.DATA};

        Cursor cursor = contentResolver.query(selectedVideoUri, filePathColumn, null, null, null);
        cursor.moveToFirst();

        int columnIndex = cursor.getColumnIndex(filePathColumn[0]);
        filePath = cursor.getString(columnIndex);
        cursor.close();
        return filePath;
    }

    public void showToast(final String text) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                Toast.makeText(VideoCaptureActivity.this, text, Toast.LENGTH_SHORT).show();
            }
        });
    }

    private HandlerThread mBackgroundHandlerThread;
    private Handler mBackgroundHandler;

    private void startBackgroundThread() {
        mBackgroundHandlerThread = new HandlerThread("3DScan");
        mBackgroundHandlerThread.start();
        mBackgroundHandler = new Handler(mBackgroundHandlerThread.getLooper());
    }

    private void stopBackgroundThread() {
        mBackgroundHandlerThread.quitSafely();
        try {
            mBackgroundHandlerThread.join();
            mBackgroundHandlerThread = null;
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

    }

    private static int sensorToDeviceRotation(CameraCharacteristics cameraCharacteristics,
                                              int deviceOrientation) {
        int sensorOrientation = cameraCharacteristics.get(CameraCharacteristics.SENSOR_ORIENTATION);
        deviceOrientation = ORIENTATIONS.get(deviceOrientation);
        return (sensorOrientation + deviceOrientation + 360) % 360;
        // FIXME: what is sensorOri and devicOri?
    }

    /**
     * A helper class that is used in {@link #setupCamera(int, int)} to choose the optimal size for camera preview
     */
    private static class CompareSizeByArea implements Comparator<Size> {

        @Override
        public int compare(Size lhs, Size rhs) {
            return Long.signum((long) lhs.getWidth() * rhs.getHeight() /
                    (long) rhs.getWidth() * rhs.getHeight());
        }
    }

    private static Size chooseOptimalSize(Size[] choices, int width, int height) {
        // FIXME: what does this means?
        Size bigEnough = null;
        int minAreaDiff = Integer.MAX_VALUE;
        for (Size option : choices) {
            int diff = (width*height)-(option.getWidth()*option.getHeight()) ;
            if (diff >=0 && diff < minAreaDiff &&
                    option.getWidth() <= width &&
                    option.getHeight() <= height) {
                minAreaDiff = diff;
                bigEnough = option;
            }
        }
        if (bigEnough != null) {
            return bigEnough;
        } else {
            Arrays.sort(choices,new CompareSizeByArea());
            return choices[0];
        }

    }

    private void createAppFilesFolder() {
        File movieFile = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
        mAppFilesFolder = new File(movieFile, mAppFilesFolderName);
        if(!mAppFilesFolder.exists()) {
            mAppFilesFolder.mkdirs();
        }
    }

    public void createVideoFolder() {
        String timestamp = new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date());
        mScanFolderName = timestamp + "_" + Settings.Secure.getString(VideoCaptureActivity.this.getContentResolver(),
                Settings.Secure.ANDROID_ID);
        mScanFolder = new File(mAppFilesFolder, mScanFolderName);
        if(!mScanFolder.exists()) {
            mScanFolder.mkdirs();
        }
    }

    private File createVideoFileName() {
        // FIXME: add unique prefix in the configuration
        File videoFile = new File(mScanFolder, mScanFolderName+".mp4");
        mVideoFilePath = videoFile.getAbsolutePath();
        return videoFile;
    }

    private boolean checkLocationPermission() {
        if(ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED) {
            return true;
        } else {
            if(shouldShowRequestPermissionRationale(Manifest.permission.ACCESS_FINE_LOCATION))
            {
                showToast("app needs to get gps information");
            }
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION},
                    REQUEST_ACCESS_FINE_LOCATION_PERMISSION_RESULT);
            return false;
        }
    }

    private boolean checkWriteStoragePermission() throws IOException {
        if(Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            if(ContextCompat.checkSelfPermission(this, Manifest.permission.WRITE_EXTERNAL_STORAGE)
                    == PackageManager.PERMISSION_GRANTED) {
                createVideoFolder();
                createVideoFileName();
                return true;
            } else {
                if(shouldShowRequestPermissionRationale(Manifest.permission.WRITE_EXTERNAL_STORAGE))
                {
                    showToast("app needs to be able to save videos");
                }
                requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE},
                        REQUEST_WRITE_EXTERNAL_STORAGE_PERMISSION_RESULT);
                return false;
            }
        } else {
            createVideoFolder();
            createVideoFileName();
            return true;
        }
    }

    private void setupMediaRecorder() throws IOException {
        mMediaRecorder.setVideoSource(MediaRecorder.VideoSource.SURFACE);
        mMediaRecorder.setOutputFormat(MediaRecorder.OutputFormat.MPEG_4);

        mMediaRecorder.setVideoEncodingBitRate(mBitRate);
        mMediaRecorder.setVideoEncoder(MediaRecorder.VideoEncoder.H264);

        mMediaRecorder.setVideoSize(mVideoSize.getWidth(), mVideoSize.getHeight());
        mMediaRecorder.setVideoFrameRate(mFrameRate);

        mMediaRecorder.setOutputFile(mVideoFilePath);

        mMediaRecorder.setOrientationHint(mTotalRotation);
        mMediaRecorder.prepare();
    }

}