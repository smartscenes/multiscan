package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.fio;

import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.zip.Deflater;
import java.util.zip.DeflaterOutputStream;

/**
 * A CustomFileWriter class that write text data to local storage
 */
public class CustomFileWriter {
    public final String dir;

    public CustomFileWriter(String myPathToFolder){
        dir = myPathToFolder;
    }

    public void writeFile(String info, String fileName) {
        try {
            File file = new File(dir, fileName);

            if (!file.exists())
                file.createNewFile();

            FileWriter fileWriter = new FileWriter(file, true);
            fileWriter.write(info);
            fileWriter.write(System.lineSeparator());
            fileWriter.close();
        }
        catch (Exception e){
            Log.d("FileWriter", "Error writing file");
        }
    }

    public void writeOutputStream(ByteBuffer byteBuffer, String fileName) {
        try {
            File file = new File(dir, fileName);
            if (!file.exists())
                file.createNewFile();
            FileOutputStream fileOutputStream = new FileOutputStream(file, true);
            OutputStream outputStream = new DeflaterOutputStream(
                    fileOutputStream, new Deflater(Deflater.DEFAULT_COMPRESSION, true));
            outputStream.write(getByteArrayFromByteBuffer(byteBuffer));
            outputStream.flush();
            outputStream.close();
            fileOutputStream.flush();
            fileOutputStream.close();
        }
        catch (Exception e) {
            Log.d("FileWriter", "Error writing compressed file");
            Log.d("FileWriter", e.toString());
        }
    }

    public void writeBinaryOutputStream(ByteBuffer byteBuffer, String fileName) {
        try {
            byteBuffer.position(0);
            File file = new File(dir, fileName);
            if (!file.exists())
                file.createNewFile();
            OutputStream outputStream = new FileOutputStream(file, true);
            outputStream.write(getByteArrayFromByteBuffer(byteBuffer));
            outputStream.flush();
            outputStream.close();
        }
        catch (Exception e) {
            Log.d("FileWriter", "Error writing compressed file");
            Log.d("FileWriter", e.toString());
        }
    }

    private  byte[] getByteArrayFromByteBuffer(ByteBuffer byteBuffer) {
        byte[] bytesArray = new byte[byteBuffer.remaining()];
        byteBuffer.get(bytesArray, 0, bytesArray.length);
        return bytesArray;
    }
}
