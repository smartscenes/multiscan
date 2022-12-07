package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp;

import android.Manifest;
import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationManager;
import android.media.Image;
import android.media.MediaMetadataRetriever;
import android.opengl.GLES20;
import android.opengl.GLSurfaceView;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.Settings;
import android.util.Log;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.CompoundButton;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.Switch;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.preference.PreferenceManager;

import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.fio.CustomCompressor;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.fio.CustomFileWriter;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.fio.CustomStreamWriterManager;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.helpers.DepthTextureHandler;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.helpers.DisplayRotationHelper;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.helpers.PermissionHelper;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.helpers.SnackbarHelper;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.helpers.TrackingStateHelper;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.model.CameraFrameInfo;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.model.CameraInfo;
import com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.rendering.BackgroundRenderer;
import com.google.android.material.floatingactionbutton.FloatingActionButton;
import com.google.ar.core.ArCoreApk;
import com.google.ar.core.Camera;
import com.google.ar.core.CameraConfig;
import com.google.ar.core.CameraConfigFilter;
import com.google.ar.core.Config;
import com.google.ar.core.Frame;
import com.google.ar.core.RecordingConfig;
import com.google.ar.core.Session;
import com.google.ar.core.TrackingState;
import com.google.ar.core.exceptions.CameraNotAvailableException;
import com.google.ar.core.exceptions.RecordingFailedException;
import com.google.ar.core.exceptions.UnavailableApkTooOldException;
import com.google.ar.core.exceptions.UnavailableArcoreNotInstalledException;
import com.google.ar.core.exceptions.UnavailableDeviceNotCompatibleException;
import com.google.ar.core.exceptions.UnavailableSdkTooOldException;
import com.google.ar.core.exceptions.UnavailableUserDeclinedInstallationException;

import java.io.File;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.ShortBuffer;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

import static com.google.ar.core.ArCoreApk.Availability.SUPPORTED_NOT_INSTALLED;

//Reference: https://codelabs.developers.google.com/codelabs/arcore-depth#6

/**
 * ARCore activity that let user record the rgb frames, depth frames and depth confidence maps using Google's <a href="https://developers.google.com/ar/develop"> ARCore </a>
 */
public class ARCoreVideoCaptureActivity extends AppCompatActivity implements GLSurfaceView.Renderer {
    private boolean isRecording;
    private boolean isDepthSupported;
    private boolean showDepthMap;
    private boolean isARCoreInstalled;

    private Session session;
    private CameraInfo cameraInfo;
    private CustomFileWriter customFileWriter;
    private CustomStreamWriterManager customStreamWriterManager;
    private GLSurfaceView glSurfaceView;
    private DisplayRotationHelper displayRotationHelper;
    private RecordingConfig recordingConfig;
    private final SnackbarHelper messageSnackbarHelper = new SnackbarHelper();
    private final TrackingStateHelper trackingStateHelper = new TrackingStateHelper(this);

    private final DepthTextureHandler depthTexture = new DepthTextureHandler();
    private final BackgroundRenderer backgroundRenderer = new BackgroundRenderer();

    private final String TAG = "ARCore_Activity";
    private File mAppFilesFolder;
    private String videoFileFullPath;
    private String fileName;
    private String currentFolderPath;
    private File metaDataFile;
    private File cameraInfoFile;
    private File depthInfoFile;
    private File depthConfidenceFile;
    private Boolean depthDataWritten;
    private Boolean isDebugMode;

    // Used to match frames at the end
    ByteBuffer depthRangeByteBuffer;
    ByteBuffer wrapConfidenceData;
    CameraFrameInfo cameraFrameInfo;
    int frameCount;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_arcore_video_capture);

        displayRotationHelper = new DisplayRotationHelper(this);
        cameraInfo = new CameraInfo();
        glSurfaceView = findViewById(R.id.surfaceView);
        isRecording = false;
        isARCoreInstalled = false;
        showDepthMap = false;
        depthDataWritten = false;
        isDebugMode = false;
        frameCount = 0;
        currentFolderPath = "";

        checkIfARCoreInstalled();
        setUpRecordButton();
        setUpDepthMapSwitch();
        setUpRenderer();
        createAppFolder();
    }

    /**
     * Display a config dialog to user and let user select rgb frame resolution
     */
    private void showRecordingConfigDialog() {
        final View view = getLayoutInflater().inflate(R.layout.arcore_recording_config_dialog, null);
        prePopulateSpinner(view);
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setView(view)
                .setCancelable(false);
        builder.setPositiveButton("Confirm", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                Spinner spinner = view.findViewById(R.id.sceneType_spinner);
                getIntent().putExtra(TAG, spinner.getSelectedItemPosition());
                if (spinner.getSelectedItemPosition() != 0)
                    recreate();

            }
        });

        builder.setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                finish();
            }
        });
        builder.show();
    }

    /**
     * Populate the spinner based the current phone's config
     * @param view the spinner view
     * @see #showRecordingConfigDialog(){@link #showRecordingConfigDialog()}
     */
    private void prePopulateSpinner(View view) {
        Spinner spinner = view.findViewById(R.id.sceneType_spinner);
        ArrayList<String> list = new ArrayList<>();

        CameraConfigFilter cameraConfigFilter = new CameraConfigFilter(session);
        List<CameraConfig> cameraConfigList = session.getSupportedCameraConfigs(cameraConfigFilter);
        // ! get the last 3 camera configs
        cameraConfigList = cameraConfigList.subList(Math.max(0, cameraConfigList.size() - 3), cameraConfigList.size());
        for (CameraConfig cameraConfig : cameraConfigList) {
            list.add(cameraConfig.getFpsRange().toString() + ", " + cameraConfig.getImageSize().toString());
        }

        ArrayAdapter<String> fpsArrayAdapter = new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_item, list);
        fpsArrayAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinner.setAdapter(fpsArrayAdapter);
    }

    private void checkIfARCoreInstalled() {
        ArCoreApk.Availability availability = ArCoreApk.getInstance().checkAvailability(this);
        if (availability == SUPPORTED_NOT_INSTALLED) {
            try {
                ArCoreApk.getInstance().requestInstall(this, true);
            } catch (Exception e) {
                Toast.makeText(this,
                        "ARCore is needed to use this feature", Toast.LENGTH_LONG).show();

            }
            finish();
        }
    }

    /**
     * Create the folder that will store all the data about the current scan
     */
    private void createAppFolder() {
        String mAppFilesFolderName = MainActivity.appFilesFolderName;

        File movieFile = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
        mAppFilesFolder = new File(movieFile, mAppFilesFolderName);

        if (!mAppFilesFolder.exists()) {
            mAppFilesFolder.mkdirs();
        }
    }

    /**
     * Setting up the switch button so the user can switch between rgb view and depth view
     */
    private void setUpDepthMapSwitch() {
        Switch depthSwitch = findViewById(R.id.showDepth_switch);
        depthSwitch.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {
            @Override
            public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
                showDepthMap = isChecked;
            }
        });
    }

    @Override
    protected void onResume() {
        super.onResume();

        if (session == null)
            createARSession();

        // Note that order matters - see the note in onPause(), the reverse applies here.
        resumeARSession();

        glSurfaceView.onResume();
        displayRotationHelper.onResume();
    }

    private void resumeARSession() {
        try {
            session.resume();
        } catch (CameraNotAvailableException e) {
            messageSnackbarHelper.showError(this, "Camera not available. Try restarting the app.");
            session = null;
            return;
        }
    }

    private void createARSession() {
        Exception exception = null;
        String message = null;
        try {
            switch (ArCoreApk.getInstance().requestInstall(this, isARCoreInstalled)) {
                case INSTALL_REQUESTED:
                    isARCoreInstalled = true;
                    return;
                case INSTALLED:
                    break;
            }

            // ARCore requires camera permissions to operate. If we did not yet obtain runtime
            // permission on Android M and above, now is a good time to ask the user for it.
            if (!(PermissionHelper.hasCameraPermission(this)
                    && PermissionHelper.hasWriteStoragePermission(this))) {
                PermissionHelper.requestCameraAndWriteExternalStoragePermission(this);
                return;
            }

            // Creates the ARCore session.
            session = new Session(/* context= */ this);
            Config config = session.getConfig();

            // Ask the user for the recording config (resolution)
            if (getIntent().getExtras() == null) {
                showRecordingConfigDialog();
                CameraConfigFilter cameraConfigFilter = new CameraConfigFilter(session);
                List<CameraConfig> cameraConfigList = session.getSupportedCameraConfigs(cameraConfigFilter);
                session.setCameraConfig(cameraConfigList.get(0));
            } else {
                CameraConfigFilter cameraConfigFilter = new CameraConfigFilter(session);
                List<CameraConfig> cameraConfigList = session.getSupportedCameraConfigs(cameraConfigFilter);
                // calculate the correct index since only the last three camera configs are shown to user
                int index = cameraConfigList.size() - 3 + getIntent().getExtras().getInt(TAG, 0);
                session.setCameraConfig(cameraConfigList.get(index));
            }

            isDepthSupported = session.isDepthModeSupported(Config.DepthMode.AUTOMATIC);
            if (isDepthSupported) {
                config.setDepthMode(Config.DepthMode.AUTOMATIC);
            } else {
                config.setDepthMode(Config.DepthMode.DISABLED);
            }
            session.configure(config);

        } catch (UnavailableArcoreNotInstalledException
                | UnavailableUserDeclinedInstallationException e) {
            message = "Please install ARCore";
            exception = e;
        } catch (UnavailableApkTooOldException e) {
            message = "Please update ARCore";
            exception = e;
        } catch (UnavailableSdkTooOldException e) {
            message = "Please update this app";
            exception = e;
        } catch (UnavailableDeviceNotCompatibleException e) {
            message = "This device does not support AR";
            exception = e;
        } catch (Exception e) {
            message = "Failed to create AR session";
            exception = e;
        }

        if (message != null) {
            messageSnackbarHelper.showError(this, message);
            Log.e(TAG, "Exception creating session", exception);
            return;
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        if (session != null) {
            // Note that the order matters - GLSurfaceView is paused first so that it does not try
            // to query the session. If Session is paused before GLSurfaceView, GLSurfaceView may
            // still call session.update() and get a SessionPausedException.
            displayRotationHelper.onPause();
            glSurfaceView.onPause();
            session.pause();
        }
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        /*
          Uncomment this if you want this activity to be completely full screen
          Ex: No date and battery symbol on top of the activity
         */
//        FullScreenHelper.setFullScreenOnWindowFocusChanged(this, hasFocus);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] results) {
        if (!PermissionHelper.hasCameraPermission(this)) {
            Toast.makeText(this,
                    "Camera permission is needed to run this application",
                    Toast.LENGTH_LONG).show();
            finish();
        }
        if (!PermissionHelper.hasWriteStoragePermission(this)) {
            Toast.makeText(this,
                    "Write external storage permission is needed to run this application",
                    Toast.LENGTH_LONG).show();
            finish();
        }
    }

    @Override
    public void onSurfaceCreated(GL10 gl, EGLConfig config) {
        GLES20.glClearColor(0.1f, 0.1f, 0.1f, 1.0f);

        // Prepare the rendering objects. This involves reading shaders, so may throw an IOException.
        try {
            // The depth texture is used for object occlusion and rendering.
            depthTexture.createOnGlThread();

            // Create the texture and pass it to ARCore session to be filled during update().
            backgroundRenderer.createOnGlThread(/*context=*/ this);
            backgroundRenderer.createDepthShaders(/*context=*/ this, depthTexture.getDepthTexture());
        } catch (IOException e) {
            Log.e(TAG, "Failed to read an asset file", e);
        }
    }

    @Override
    public void onSurfaceChanged(GL10 gl, int width, int height) {
        displayRotationHelper.onSurfaceChanged(width, height);
        GLES20.glViewport(0, 0, width, height);
    }

    /**
     * Each time the frame gets updated, call certain methods (EX: record the scene data if the user press record)
     * @param gl openGLSurface
     */
    @Override
    public void onDrawFrame(GL10 gl) {
        // Clear screen to notify driver it should not load any pixels from previous frame.
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT | GLES20.GL_DEPTH_BUFFER_BIT);

        if (session == null) {
            return;
        }
        // Notify ARCore session that the view size changed so that the perspective matrix and
        // the video background can be properly adjusted.
        displayRotationHelper.updateSessionIfNeeded(session);

        try {
            session.setCameraTextureName(backgroundRenderer.getTextureId());

            // Obtain the current frame from ARSession. When the configuration is set to
            // UpdateMode.BLOCKING (it is by default), this will throttle the rendering to the
            // camera frame rate.
            Frame frame = session.update();
            Camera camera = frame.getCamera();

            if (isRecording) {
                updateCameraInfo(frame, camera);
                writeDepthAndConfidenceInfo(frame, camera);
            }

            // Retrieves the latest depth image for this frame.
            if (isDepthSupported) {
                depthTexture.update(frame);
            }

            // If frame is ready, render camera preview image to the GL surface.
            backgroundRenderer.draw(frame);
            if (showDepthMap) {
                backgroundRenderer.drawDepth(frame);
            }

            // Keep the screen unlocked while tracking, but allow it to lock when tracking stops.
            trackingStateHelper.updateKeepScreenOnFlag(camera.getTrackingState());

            // If not tracking, don't draw 3D objects, show tracking failure reason instead.
            if (camera.getTrackingState() == TrackingState.PAUSED) {
                messageSnackbarHelper.showMessage(
                        this, TrackingStateHelper.getTrackingFailureReasonString(camera));
                return;
            }

            // Get projection matrix.
            float[] projmtx = new float[16];
            camera.getProjectionMatrix(projmtx, 0, 0.1f, 100.0f);

            // Get camera matrix and draw.
            float[] viewmtx = new float[16];
            camera.getViewMatrix(viewmtx, 0);

            // Compute lighting from average intensity of the image.
            // The first three components are color scaling factors.
            // The last one is the average pixel intensity in gamma space.
            final float[] colorCorrectionRgba = new float[4];
            frame.getLightEstimate().getColorCorrection(colorCorrectionRgba, 0);

            // No tracking error at this point. Inform user of what to do based on if planes are found.
            String messageToShow = "";

            if (!isDepthSupported) {
                messageToShow += "\n" + "[Depth not supported on this device]";
            }

            if (messageToShow.equals(""))
                messageSnackbarHelper.hide(this);
            else
                messageSnackbarHelper.showMessage(this, messageToShow);
        } catch (Throwable t) {
            // Avoid crashing the application due to unhandled exceptions.
            Log.e(TAG, "Exception on the OpenGL thread", t);
        }
    }

    /**
     * Write depth and confidence map to local
     * @param frame the current frame
     * @param camera the current camera, used to retrieve camera intrinsics
     */
    private void writeDepthAndConfidenceInfo(Frame frame, Camera camera) {
        try {
            cameraFrameInfo = new CameraFrameInfo(frame, camera);
            customFileWriter.writeFile(cameraFrameInfo.toJSONString(), fileName + ".jsonl");

            // Those two list is used to write the depth and confidence in txt format (debug only)
            List<String> tempRange = new ArrayList<>();
            List<String> tempConfidence = new ArrayList<>();

            // Get the depth image buffer
            Image image = frame.acquireRawDepthImage();
            ShortBuffer depthBuffer = image.getPlanes()[0].getBuffer().order(ByteOrder.LITTLE_ENDIAN).asShortBuffer();
            image.close();

            Image confidenceImage = frame.acquireRawDepthConfidenceImage();
            ByteBuffer confidenceData = confidenceImage.getPlanes()[0].getBuffer();
            confidenceImage.close();
            wrapConfidenceData = ByteBuffer.allocate(confidenceData.capacity());

            // reposition confidenceImage cursor
            confidenceData.position(0);

            // Preallocate the buffers, those two buffers will be used to write to local storage
            depthRangeByteBuffer = ByteBuffer.allocate(
                    cameraInfo.depthImageWidth * cameraInfo.depthImageHeight * Short.BYTES);
            depthRangeByteBuffer.order(ByteOrder.LITTLE_ENDIAN);

            //TODO: Uncomment block 1, 2, 3 to output confidence values (If ARCore supports it)
            // * 1
//            ByteBuffer depthConfidenceByteBuffer = ByteBuffer.allocate(
//                    cameraInfo.depthImageWidth * cameraInfo.depthImageHeight);
//            depthConfidenceByteBuffer.order(ByteOrder.LITTLE_ENDIAN);

            while (depthBuffer.hasRemaining()) {
                short depthSample = depthBuffer.get();
                short tempSampleForDebug = depthSample;

                short depthRange = (short) (depthSample & 0x1FFF);
                //a value of 0 representing 100% confidence, a value of 1 representing 0% confidence,
                //a value of 2 representing 1/7, a value of 3 representing 2/7, and so on.
                byte depthConfidence = (byte) ((depthSample >> 13) & 0x7);

                if (isDebugMode) {
                    short depthConfidenceTemp = (short) ((tempSampleForDebug >> 13) & 0x7);
                    tempRange.add(Short.toString(depthRange));
                    tempConfidence.add(Short.toString(depthConfidenceTemp));
                }
                // * 2
//                depthConfidenceByteBuffer.put(depthConfidence);
                depthRangeByteBuffer.putShort(depthRange);
                wrapConfidenceData.put(confidenceData.get());
            }

            if (isDebugMode) {
                customFileWriter.writeFile(tempConfidence.toString(), fileName + "_confidence.txt");
                customFileWriter.writeFile(tempRange.toString(), fileName + "_depth.txt");
            }

            // Write data to drive in compressed format
            try {
                customStreamWriterManager.writeToFile(fileName + ".depth.zlib", depthRangeByteBuffer);
                // * 3
//                customStreamWriterManager.writeToFile(fileName + ".confidence.zlib", depthConfidenceByteBuffer);
                customStreamWriterManager.writeToFile(fileName + ".confidence.zlib", wrapConfidenceData);
                frameCount++;
            } catch (Exception e) {
                Log.d(TAG, "Error writing depth and confidence values");
                Log.d(TAG, e.toString());
            }
        } catch (Exception e) {
            Log.d(TAG, "Error writing depth info");
            Log.d(TAG, e.toString());
        }
    }

    /**
     * Retrieve basic camera info such as image size and write them into the metadata file
     * @param frame initial frame after user click the record button
     * @param camera initial camera after user click the record button
     */
    private void updateCameraInfo(Frame frame, Camera camera) {
        int[] imageDimension = camera.getImageIntrinsics().getImageDimensions(); // The order of values is {width, height}
        cameraInfo.imageDimensions = new int[] {
                imageDimension[1],
                imageDimension[0]}; // flip the dimension

        if (!depthDataWritten) {
            try {
                Image image = frame.acquireDepthImage();
                SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(this);

                cameraInfo.depthImageHeight = image.getHeight();
                cameraInfo.depthImageWidth = image.getWidth();
                cameraInfo.deviceName = preferences.getString("device_name", "");
                cameraInfo.userName = preferences.getString("user_name", "");
                cameraInfo.manufacturer = Build.MANUFACTURER;
                cameraInfo.modelNumber = Build.MODEL;
                cameraInfo.depthUnit = "mm";
                cameraInfo.depthConfidenceValueRange = new int[]{0, 255};
                cameraInfo.confidenceAvailable = true;
                cameraInfo.quaternionFormat = "xyzw";
                cameraInfo.depthConfidenceImageType = "Y8";
                cameraInfo.GPS = getLastBestLocation();
                depthDataWritten = true;
            } catch (Exception e) {
                Log.d(TAG, "Error getting depth Image dimension");
            }
        }
    }

    /**
     * Get location data
     * @return GPS coords [Latitude, Longitude]
     */
    private double[] getLastBestLocation() {
        LocationManager locationManager = (LocationManager) getSystemService(Context.LOCATION_SERVICE);
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED && ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[] {Manifest.permission.ACCESS_FINE_LOCATION,
                            Manifest.permission.ACCESS_COARSE_LOCATION}, 1);
        }

        Location location = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
        if (location != null) {
            return new double[] {location.getLatitude(), location.getLongitude()};
        }
        return new double[] {};
    }

    public static Intent makeIntentForMultiCameraCaptureActivity(Context context) {
        return new Intent(context, ARCoreVideoCaptureActivity.class);
    }

    private void setUpRenderer() {
        glSurfaceView.setPreserveEGLContextOnPause(true);
        glSurfaceView.setEGLContextClientVersion(2);
        glSurfaceView.setEGLConfigChooser(8, 8, 8, 8, 16, 0); // Alpha used for plane blending.
        glSurfaceView.setRenderer(this);
        glSurfaceView.setRenderMode(GLSurfaceView.RENDERMODE_CONTINUOUSLY);
        glSurfaceView.setWillNotDraw(false);
    }

    private void setUpRecordButton(){
        final FloatingActionButton floatingActionButton =
                findViewById(R.id.record_button_multi_camera_activity);

        floatingActionButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                if (isRecording) {
                    isRecording = false;

                    floatingActionButton.setImageDrawable(
                            ContextCompat.getDrawable(
                                    getApplicationContext(), R.drawable.ic_baseline_circle_red_24));

                    try {
                        session.stopRecording();
                        Toast.makeText(ARCoreVideoCaptureActivity.this,
                                "Recording Stopped", Toast.LENGTH_SHORT).show();

                        AlertDialog.Builder builder = new AlertDialog.Builder(ARCoreVideoCaptureActivity.this);
                        builder.setCancelable(false); // if you want user to wait for some process to finish,
                        builder.setView(R.layout.arcore_data_processing_dialog);
                        final AlertDialog dialog = builder.create();
                        dialog.setTitle("Please wait");
                        dialog.show();

                        new Thread(new Runnable() {
                            @Override
                            public void run() {
                                int rgbFrame = updateFrameCount();
                                writeMetadataFile();
                                matchFrames(rgbFrame);
                                try {
                                    customStreamWriterManager.closeAllWriters();
                                } catch (Exception e) {
                                    Log.d(TAG, "Error closing customStreamWriterManager");
                                }
                                dialog.dismiss();
                            }
                        }).start();

                    } catch (RecordingFailedException e) {
                        Log.e(TAG, "Failed to stop recording", e);
                    }
                }
                else {
                    showContentDescriptionDialog();
                }
            }
        });
    }

    private void matchFrames(int rgbFrame) {
        if(rgbFrame > frameCount) {
            for (int i = 0; i < rgbFrame - frameCount; i++) {
                try {
                    customStreamWriterManager.writeToFile(fileName + ".depth.zlib", depthRangeByteBuffer);
                    customStreamWriterManager.writeToFile(fileName + ".confidence.zlib", wrapConfidenceData);
                    cameraFrameInfo.timestamp = System.nanoTime();
                    customFileWriter.writeFile(cameraFrameInfo.toJSONString(), fileName + ".jsonl");
                } catch (Exception e) {
                    Log.d(TAG, "Error matching depth and rgb frames");
                    Log.d(TAG, e.toString());
                }
            }
        }
    }

    /**
     * Compress depth and confidence files
     */
    private void compressTempFiles() {
        File depthRangeTempFile = new File(currentFolderPath, fileName + "_depth.temp");
        File depthConfidenceTempFile = new File(currentFolderPath, fileName + "_confidence.temp");

        try {
            CustomCompressor.compressFile(depthRangeTempFile, depthInfoFile);
            CustomCompressor.compressFile(depthConfidenceTempFile, depthConfidenceFile);

            if (depthRangeTempFile.delete() & depthConfidenceTempFile.delete())
                Log.d(TAG, "Temp file not successfully deleted");
        }
        catch (Exception e) {
            Log.d("FileWriter", "Error writing compressed file");
            Log.d("FileWriter", e.toString());
        }
    }

    /**
     * Retrieve number of frames for the video
     * @return number of frames
     */
    private int updateFrameCount() {
        MediaMetadataRetriever retriever = new MediaMetadataRetriever();
        retriever.setDataSource(videoFileFullPath);
        cameraInfo.frameCount = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_VIDEO_FRAME_COUNT);
        return Integer.parseInt(cameraInfo.frameCount);
    }

    /**
     * Write metadata file to local storage
     */
    private void writeMetadataFile() {
        try{
            customFileWriter.writeFile(cameraInfo.toJSONString(), fileName + ".json");
        } catch (Exception e) {
            Log.d(TAG, "Error writing CameraInfo");
        }
    }

    /**
     * Show a dialog and ask user to enter scene type and description of the scene
     */
    private void showContentDescriptionDialog() {
        final View view = getLayoutInflater().inflate(R.layout.arcore_recording_info_dialog, null);
        AlertDialog.Builder builder = new AlertDialog.Builder(ARCoreVideoCaptureActivity.this);
        builder.setView(view)
                .setCancelable(false);

        builder.setPositiveButton("Start Recording", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                Spinner spinner = view.findViewById(R.id.sceneType_spinner);
                String sceneType = spinner.getSelectedItem().toString();
                EditText editText = view.findViewById(R.id.description_editText);
                String description = editText.getText().toString();

                ARSessionStartRecord();

                cameraInfo.sceneType = sceneType;
                cameraInfo.description = description;
                depthDataWritten = false;
                customFileWriter = new CustomFileWriter(currentFolderPath);

                customStreamWriterManager = new CustomStreamWriterManager(currentFolderPath);
                try {
                    customStreamWriterManager.addWriter(fileName + ".depth.zlib");
                    customStreamWriterManager.addWriter(fileName + ".confidence.zlib");
                } catch (Exception e) {
                    Log.d(TAG, "Error adding writers to customStreamWriterManager");
                }


                isRecording = true;
            }
        });
        builder.setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                dialog.dismiss();
            }
        });

        builder.show();
    }

    private void ARSessionStartRecord() {
        final FloatingActionButton floatingActionButton =
                findViewById(R.id.record_button_multi_camera_activity);

        setupARRecordingConfig();

        try {
            checkIsDebug();
            session.startRecording(recordingConfig);
            floatingActionButton.setImageDrawable(
                    ContextCompat.getDrawable(
                            getApplicationContext(), R.drawable.ic_baseline_stop_black_32));
        } catch (RecordingFailedException e) {
            Log.e(TAG, "Failed to start recording", e);
        }
        Toast.makeText(ARCoreVideoCaptureActivity.this,
                "Recording Started", Toast.LENGTH_SHORT).show();
    }

    /**
     * Check if the App is running in debug mode
     */
    private void checkIsDebug() {
        SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(this);
        isDebugMode = preferences.getBoolean("debug_flag", false);
    }

    /**
     * Setting up rgb video and set the recording resolution
     */
    private void setupARRecordingConfig() {
        videoFileFullPath = new File(createVideoAndFileFolder(), fileName + ".mp4").getAbsolutePath();
        recordingConfig =
                new RecordingConfig(session)
                        .setMp4DatasetFilePath(videoFileFullPath)
                        .setAutoStopOnPause(false);
    }

    /**
     * Create the video file for recording
     * @return absolute path of the video file
     */
    private String createVideoAndFileFolder() {
        String timestamp = new SimpleDateFormat("yyyyMMdd'T'HHmmssZ").format(new Date());
        fileName = timestamp + "_" + Settings.Secure.getString(this.getContentResolver(),
                Settings.Secure.ANDROID_ID);
        File mScanFolder = new File(mAppFilesFolder, fileName);
        if(!mScanFolder.exists()) {
            mScanFolder.mkdirs();
        }
        currentFolderPath = mScanFolder.getAbsolutePath();
        createFiles(fileName);

        return mScanFolder.getAbsolutePath();
    }

    /**
     * Create all the files to store data such as depth data and confidence map
     * @param fileName filename prefix
     */
    private void createFiles(String fileName) {
        try {
            metaDataFile = new File(currentFolderPath, fileName + ".json");
            cameraInfoFile = new File(currentFolderPath, fileName + ".jsonl");
            depthInfoFile = new File(currentFolderPath, fileName + ".depth.zlib");
            depthConfidenceFile = new File(currentFolderPath, fileName + ".confidence.zlib");
        } catch (Exception e) {
            Log.d(TAG, "Error creating files");
        }
    }
}
