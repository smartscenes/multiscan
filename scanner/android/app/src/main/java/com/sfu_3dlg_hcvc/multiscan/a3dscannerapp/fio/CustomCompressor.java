package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp.fio;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.zip.Deflater;
import java.util.zip.DeflaterOutputStream;

/**
 * Compressor that will convert a file into a compressed file using a Deflater
 */
public class CustomCompressor {
    public static void compressFile(File raw, File compressed) throws IOException
    {
        InputStream in = new FileInputStream(raw);
        OutputStream out =
                new DeflaterOutputStream(new FileOutputStream(compressed), new Deflater(Deflater.DEFAULT_COMPRESSION, true));
        shovelInToOut(in, out);
        in.close();
        out.close();
    }

    private static void shovelInToOut(InputStream in, OutputStream out)
            throws IOException
    {
        byte[] buffer = new byte[1000];
        int len;
        while((len = in.read(buffer)) > 0) {
            out.write(buffer, 0, len);
        }
    }
}
