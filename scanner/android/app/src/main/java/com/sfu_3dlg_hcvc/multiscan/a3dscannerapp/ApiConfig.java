package com.sfu_3dlg_hcvc.multiscan.a3dscannerapp;

import okhttp3.MultipartBody;
import okhttp3.RequestBody;
import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.Header;
import retrofit2.http.Multipart;
import retrofit2.http.POST;
import retrofit2.http.PUT;
import retrofit2.http.Part;
import retrofit2.http.Query;
import retrofit2.http.Url;

/**
 * API config used for {@link ARCoreVideoCaptureActivity}
 */
interface ApiConfig {
    @Multipart
    @POST("uploadVideo")
    Call<ResponseBody> uploadVideo(
            @Part MultipartBody.Part file
    );


    @PUT("multiscan/upload")
    Call<ResponseBody> upload(
            @Header("FILE_NAME") String filename,
            @Body RequestBody body
    );

    @PUT
    Call<ResponseBody> uploadFullUrl(
            @Url String url,
            @Header("FILE_NAME") String filename,
            @Body RequestBody body
    );

    @GET
    Call<ResponseBody>  verifyFullUrl(
            @Url String url,
            @Query("filename") String filename,
            @Query("checksum") String checksum
    );
}