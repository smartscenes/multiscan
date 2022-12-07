package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp;

import android.net.Uri;
import android.os.Bundle;
import android.widget.VideoView;

import androidx.appcompat.app.AppCompatActivity;

/**
 * Replay recorded rgb video
 */
public class VideoPlayActivity extends AppCompatActivity {

    private VideoView mVideoView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_video_play);
        mVideoView = findViewById(R.id.videoView);

        Uri videoUri = Uri.parse(getIntent().getStringExtra("videoUri"));
        mVideoView.setVideoURI(videoUri);
        mVideoView.start();
    }
}
