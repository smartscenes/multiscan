package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.helpers;

import android.media.MediaCodec;
import android.media.MediaFormat;
import android.media.MediaMuxer;
import android.util.Log;

import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.ByteBuffer;

public class VideoEncoderHelper {
    private final static String TAG = "VideoEncoderHelper";
    private MediaCodec mediaCodec;
    private MediaMuxer mediaMuxer;
    private int frameCount = 0;
    private BufferedOutputStream bufferedOutputStream;
    private final int mWidth;
    private final int mHeight;
    private final int mFrameRate;
    private final int mBitrate;

    public int getFrameCount() {
        return frameCount;
    }

    public VideoEncoderHelper(int mWidth, int mHeight, int mFrameRate, int mBitrate, File file) {
        this.mWidth = mWidth;
        this.mHeight = mHeight;
        this.mFrameRate = mFrameRate;
        this.mBitrate = mBitrate;

        configureMediaCodec();
        configureMediaMuxer(file);
    }

    private void configureMediaCodec() {
        MediaFormat mediaFormat = MediaFormat.createVideoFormat(
                MediaFormat.MIMETYPE_VIDEO_AVC, mWidth, mHeight);
        mediaFormat.setInteger(MediaFormat.KEY_BIT_RATE, mBitrate);
        mediaFormat.setInteger(MediaFormat.KEY_FRAME_RATE, mFrameRate);
        try {
            mediaCodec = MediaCodec.createEncoderByType("video/avc");
        }
        catch (Exception e) {
            Log.d(TAG, e.toString());
        }
        mediaCodec.configure(mediaFormat, null, null, MediaCodec.CONFIGURE_FLAG_ENCODE);
        mediaCodec.start();
    }

    private void configureMediaMuxer(File file) {
        try {
            mediaMuxer = new MediaMuxer(file.getAbsolutePath(), MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4);
        }
        catch (Exception e) {
            Log.d(TAG, e.toString());
        }
    }

    public void encode(ByteBuffer byteBuffer, int byteBufferSize , long timestamp) {
        int inputBufIndex = mediaCodec.dequeueInputBuffer(0);

        if (inputBufIndex >= 0) {
            final ByteBuffer inputBuffer = mediaCodec.getInputBuffer(inputBufIndex);
            inputBuffer.clear();
            inputBuffer.put(byteBuffer);
            mediaCodec.queueInputBuffer(inputBufIndex, 0, byteBufferSize, timestamp, 0);
            frameCount++;
        }

        MediaCodec.BufferInfo bufferInfo = new MediaCodec.BufferInfo();
        int encoderStatus = mediaCodec.dequeueOutputBuffer(bufferInfo, 0);

        if (encoderStatus == MediaCodec.INFO_TRY_AGAIN_LATER) {
            // no output available yet
            Log.d(TAG, "no output from encoder available");
        } else if (encoderStatus == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED) {
            // not expected for an encoder
            MediaFormat newFormat = mediaCodec.getOutputFormat();
            mediaMuxer.addTrack(newFormat);
            mediaMuxer.start();
        } else if (encoderStatus < 0) {
            Log.i(TAG, "unexpected result from encoder.dequeueOutputBuffer: " + encoderStatus);
        } else if (bufferInfo.size != 0) {
            ByteBuffer encodedData = mediaCodec.getOutputBuffer(encoderStatus);
            if (encodedData == null) {
                Log.i(TAG, "encoderOutputBuffer " + encoderStatus + " was null");
            } else {
                encodedData.position(bufferInfo.offset);
                encodedData.limit(bufferInfo.offset + bufferInfo.size);
                mediaMuxer.writeSampleData(0, encodedData, bufferInfo);
                mediaCodec.releaseOutputBuffer(encoderStatus, false);
            }
        }
    }

    private void release() {
        if (mediaCodec != null) {
            mediaCodec.stop();
            mediaCodec.release();
            mediaCodec = null;
        }
        if (mediaMuxer != null) {
            mediaMuxer.stop();
            mediaMuxer.release();
            mediaMuxer = null;
        }
    }

    private void createFile(File file) {
        try {
            bufferedOutputStream = new BufferedOutputStream(new FileOutputStream(file));
        }
        catch (Exception e) {
            Log.d(TAG, e.toString());
        }
    }
}
