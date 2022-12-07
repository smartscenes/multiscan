package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.fio;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.util.zip.Deflater;
import java.util.zip.DeflaterOutputStream;

/**
 * A single stream writer object that will write compressed stream to local storage
 */
public class CustomStreamWriter {
    private final FileOutputStream fileOutputStream;
    private final OutputStream outputStream;

    public CustomStreamWriter(File file) throws FileNotFoundException {
        fileOutputStream = new FileOutputStream(file, true);
        outputStream = new DeflaterOutputStream(
                fileOutputStream, new Deflater(Deflater.DEFAULT_COMPRESSION, true)
        );
    }

    public void write(ByteBuffer byteBuffer) throws IOException {
        outputStream.write(byteBuffer.array());
        outputStream.flush();
        fileOutputStream.flush();
    }

    public void close() throws IOException{
        outputStream.flush();
        outputStream.close();
        fileOutputStream.flush();
        fileOutputStream.close();
    }
}
