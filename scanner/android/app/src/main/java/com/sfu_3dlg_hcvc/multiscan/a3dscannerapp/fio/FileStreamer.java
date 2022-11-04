package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.fio;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.util.Log;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.security.KeyException;
import java.util.HashMap;

/**
 * File Streamer class that is used to write to phone's local storage used in {@link com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.VideoCaptureActivity}
 */
public class FileStreamer {
    private final static int SENSOR_BYTE_LENGTH = 8;
    private final static String LOG_TAG = FileStreamer.class.getSimpleName();

    private Context mContext;

    private HashMap<String, BufferedWriter> mFileWriters = new HashMap<>();
    public HashMap<String, File> mFiles = new HashMap<>();
    private String mOutputFolder;

    public FileStreamer(Context context, final String outputFolder){
        mContext = context;
        mOutputFolder = outputFolder;
    }

    public void addFileWriter(final String writerId, final String fileName) throws IOException {
        if(mFileWriters.containsKey(writerId)){
            Log.w(LOG_TAG, "File writer" + writerId + " already exist");
            return;
        }
        BufferedWriter newWriter = createFile(mOutputFolder + "/" + fileName, "");
        mFileWriters.put(writerId, newWriter);
    }

    public void addFile(final String writerId, final String fileName, boolean addWriter) throws IOException {
        if(mFileWriters.containsKey(writerId)){
            Log.w(LOG_TAG, "File" + writerId + " already exist");
            return;
        }
        File file = new File(mOutputFolder, fileName);
        mFiles.put(writerId, file);
        if(addWriter){
            addFileWriter(writerId, fileName);
        }
    }

    private BufferedWriter createFile(String path, String header) throws IOException {
        File file = new File(path);
        BufferedWriter writer = new BufferedWriter(new FileWriter(file));
        Intent scanIntent = new Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE);
        scanIntent.setData(Uri.fromFile(file));
        mContext.sendBroadcast(scanIntent);
        if (header != null && header.length() != 0) {
            writer.append(header);
            writer.flush();
        }
        return writer;
    }

    public String getOutputFolder(){
        return mOutputFolder;
    }

    public BufferedWriter getFileWriter(final String writerId){
        return mFileWriters.get(writerId);
    }

    public File getFile(final String writerId) {
        return mFiles.get(writerId);
    }

    public void addRecord(long timestamp, String writerId, int numValues, final float[] values, final String type) throws IOException, KeyException {
        synchronized (this){
            if (type.equals("byte")) {

                File file= getFile(writerId);
                if (file == null){
                    throw new KeyException("File writer " + writerId + " not found");
                }

                FileOutputStream fos = null;
                try {
                    fos = new FileOutputStream(file, true);
                    // Writes bytes from the specified byte array to this file output stream
                    ByteBuffer time_bytes = ByteBuffer.allocate(SENSOR_BYTE_LENGTH);
                    time_bytes.order(ByteOrder.BIG_ENDIAN);
                    time_bytes.putLong(timestamp);
                    fos.write(time_bytes.array());
                    for(int i=0; i<numValues; i++) {
                        float val = values[i];
                        byte[] data_bytes = ByteBuffer.allocate(SENSOR_BYTE_LENGTH).order(ByteOrder.BIG_ENDIAN).putDouble((double)val).array();
                        fos.write(data_bytes);
                    }
                }
                catch (FileNotFoundException e) {
                    System.out.println("File not found" + e);
                }
                catch (IOException ioe) {
                    System.out.println("Exception while writing file " + ioe);
                }
                finally {
                    // close the streams using close method
                    try {
                        if (fos != null) {
                            fos.close();
                        }
                    }
                    catch (IOException ioe) {
                        System.out.println("Error while closing stream: " + ioe);
                    }
                }
            }
            else {
                // raw output
                BufferedWriter writer = getFileWriter(writerId);
                if (writer == null){
                    throw new KeyException("File writer " + writerId + " not found");
                }
                StringBuilder stringBuilder = new StringBuilder();
                stringBuilder.append(timestamp);
                for(int i=0; i<numValues; ++i){
                    stringBuilder.append(" " + Double.toString((double)values[i]));
                }
                stringBuilder.append("\n");
                writer.write(stringBuilder.toString());
            }

        }
    }

    public void endFiles() throws IOException {
        synchronized (this){
            for (BufferedWriter w : mFileWriters.values()) {
                w.flush();
                w.close();
            }
        }
    }
}
