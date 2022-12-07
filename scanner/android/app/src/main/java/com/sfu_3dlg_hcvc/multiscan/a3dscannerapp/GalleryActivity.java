package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp;

import android.content.Intent;
import android.graphics.Bitmap;
import android.media.MediaMetadataRetriever;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.TableLayout;
import android.widget.TableRow;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.io.File;
import java.io.FileInputStream;
import java.net.URLConnection;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;

import wseemann.media.FFmpegMediaMetadataRetriever;

/**
 * Shows user all previous scans and let users rewatch the previous scans and upload them to the server
 */
public class GalleryActivity extends AppCompatActivity {

    private String mAppFilesFolderName = MainActivity.appFilesFolderName;

    TableLayout mGalleryTable;
    Intent mVideoPlayIntent;
    Intent mServerUploadIntent;
    private String mDescriptionText = "";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_gallery);


        mGalleryTable = (TableLayout) findViewById(R.id.galleryTable);
        mVideoPlayIntent = new Intent(this, VideoPlayActivity.class);
        mVideoPlayIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);

        mServerUploadIntent = new Intent(this, ServerUploadActivity.class);

        createGalleryRowThread.start();
    }

    public static boolean isVideoFile(String path) {
        String mimeType = URLConnection.guessContentTypeFromName(path);
        return mimeType != null && mimeType.startsWith("video");
    }

    public static Bitmap retrieveVideoFrameFromVideo(String videoPath)
            throws Throwable {
        Bitmap bitmap = null;
        FileInputStream inputStream = null;
        MediaMetadataRetriever mediaMetadataRetriever = null;
        FFmpegMediaMetadataRetriever retriever = new  FFmpegMediaMetadataRetriever();
        try {
            inputStream = new FileInputStream(videoPath);
            mediaMetadataRetriever = new MediaMetadataRetriever();
            mediaMetadataRetriever.setDataSource(inputStream.getFD());

            bitmap = mediaMetadataRetriever.getFrameAtTime(1, MediaMetadataRetriever.OPTION_CLOSEST_SYNC);
        } catch (Exception e) {
            e.printStackTrace();
            throw new Throwable(
                    "Exception in retriveVideoFrameFromVideo(String videoPath)"
                            + e.getMessage());

        } finally {
            if (retriever != null) {
                retriever.release();
            }
            if (inputStream != null) {
                inputStream.close();
            }
        }
        return bitmap;
    }

    Thread createGalleryRowThread = new Thread() {
        @Override
        public void run() {
            File movieFile = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS);
            File appFilesFolder = new File(movieFile, mAppFilesFolderName);
            if (appFilesFolder.exists()) {
                File[] files = appFilesFolder.listFiles();
//                Arrays.sort(files, new Comparator<File>(){
//                    public int compare(File f1, File f2)
//                    {
//                        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd_HHmmss");
//                        try {
//                            Date d1 = sdf.parse(f1.getName().substring(0, 15));
//                            Date d2 = sdf.parse(f1.getName().substring(0, 15));
//                            return d1.compareTo(d2);
//                        }
//                        catch (Exception e) {
//                            e.printStackTrace();
//                        }
//                        return 0;
//                    } });
                Arrays.sort(files, new Comparator<File>(){
                    public int compare(File f1, File f2)
                    {
                        return Long.valueOf(f2.lastModified()).compareTo(f1.lastModified());
                    } });
                for (File inFile1 : files) {
                    if (inFile1.isDirectory()) {
                        String folderName = inFile1.getName();
                        File videoFile = new File(inFile1.getAbsolutePath(), folderName+".mp4");
                        if(isVideoFile(videoFile.getAbsolutePath())){
                            createGalleryRow(folderName, inFile1.getAbsolutePath());
                        }
                    }
                }
            }
        }
    };


    public void createGalleryRow(final String folderName, final String folderPath) {
//        TableLayout tl = (TableLayout) findViewById(R.id.galleryTable);
        Bitmap bitmap = null;
        final File videoFile = new File(folderPath, folderName+".mp4");
        try {
            bitmap = retrieveVideoFrameFromVideo(videoFile.getAbsolutePath());
        } catch (Throwable e) {
            e.printStackTrace();
        }
        if (bitmap != null) {
            bitmap = Bitmap.createScaledBitmap(bitmap, 240, 240, false);

            final Bitmap scaled_bitmap = bitmap;
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    TableRow row = new TableRow(GalleryActivity.this);
                    TableRow.LayoutParams lp = new TableRow.LayoutParams(TableLayout.LayoutParams.MATCH_PARENT,
                            TableRow.LayoutParams.WRAP_CONTENT);
                    lp.setMargins(5, 10, 5, 10);
                    row.setLayoutParams(lp);
                    ImageButton thumbnailBtn = new ImageButton(GalleryActivity.this);
                    thumbnailBtn.setImageBitmap(scaled_bitmap);
                    thumbnailBtn.setOnClickListener(new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                            mVideoPlayIntent.putExtra("videoUri", Uri.fromFile(videoFile).toString());
                            startActivity(mVideoPlayIntent);
                        }
                    });

                    Button uploadButton = new Button(GalleryActivity.this);
                    uploadButton.setText("upload");
                    uploadButton.setOnClickListener(new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                            String[] filesToUpload;
                            int numFiles = new File(folderPath).list().length;

                            // If the number of files in the folder == 5
                            // Then it is created from ARCore Activity
                            if(numFiles <= 5) {
                                int count = 0;
                                filesToUpload = new String[numFiles];
                                File[] fileList = new File(folderPath).listFiles();

                                for (File file : fileList) {
                                    filesToUpload[count] = file.getAbsolutePath();
                                    count++;
                                }
                            }
                            else {
                                filesToUpload = new String[]{".txt", ".mp4", ".acce", ".rot", ".grav", ".mag"};
                                int i = 0;
                                for(String ext:filesToUpload) {
                                    File f = new File(folderPath, folderName+ext);
                                    if(!f.isFile()){
                                        Toast.makeText(getApplicationContext(), f.getName() +" Not Exists!", Toast.LENGTH_SHORT).show();
                                        return;
                                    }
                                    filesToUpload[i] = f.getAbsolutePath();
                                    i++;
                                }
                            }

                            mServerUploadIntent.putExtra("fileList", filesToUpload);
                            startActivity(mServerUploadIntent);
                        }
                    });

                    TextView descriptionText = new TextView(GalleryActivity.this);
                    SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd'T'HHmmssZ");
                    try {
                        Date d = sdf.parse(videoFile.getName().substring(0, 20));
                        sdf.applyPattern("yyyy-MM-dd HH:mm:ss");
                        descriptionText.setText("Time: " + sdf.format(d));
                    } catch (ParseException e) {
                        e.printStackTrace();
                    }
                    row.addView(thumbnailBtn);
                    row.addView(descriptionText);
                    row.addView(uploadButton);
                    mGalleryTable.addView(row, lp);
                }
            });
        }
    }



}
