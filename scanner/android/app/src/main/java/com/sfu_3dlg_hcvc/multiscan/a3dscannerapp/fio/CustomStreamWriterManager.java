package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.fio;

import android.util.Log;

import java.io.File;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.HashMap;

/**
 * A stream writer manger class that can manages multiple CustomStreamWriter. Used to write multiple
 * compressed files at the same time
 */
public class CustomStreamWriterManager {
    private final String dir;
    private final HashMap<String, CustomStreamWriter> hashMap;

    public CustomStreamWriterManager(String pathToFolder) {
        this.dir = pathToFolder;
        hashMap = new HashMap<>();
    }

    public void addWriter(String fileName) throws IOException{
        File file = checkFileAndCreateFileIfNotExist(this.dir, fileName);
        hashMap.put(fileName, new CustomStreamWriter(file));
    }

    public void writeToFile(String fileName, ByteBuffer byteBuffer) throws IOException{
        this.hashMap.get(fileName).write(byteBuffer);
    }

    public void closeAllWriters() throws IOException {
        for (CustomStreamWriter customStreamWriter : hashMap.values()) {
            customStreamWriter.close();
        }
    }

    private File checkFileAndCreateFileIfNotExist(String dir, String fileName) throws IOException {
        File file = new File(dir, fileName);
        String TAG = "CustomStreamWriterManager";
        if (!file.exists())
            if (!file.createNewFile())
                Log.d(TAG, "Failed to create new file \"" + dir + fileName + "\"");

        return file;
    }
}
