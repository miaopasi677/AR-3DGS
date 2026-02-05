package com.example.inmo

import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.http.*

interface VideoApiService {
    
    @POST("stream/start")
    fun startStream(
        @Body request: StartStreamRequest
    ): Call<StartStreamResponse>
    
    @POST("stream/{streamId}/chunk")
    fun uploadChunk(
        @Path("streamId") streamId: String,
        @Body chunk: RequestBody
    ): Call<ChunkUploadResponse>
    
    @GET("stream/{streamId}")
    fun getStream(
        @Path("streamId") streamId: String
    ): Call<ResponseBody>
    
    @POST("stream/{streamId}/stop")
    fun stopStream(
        @Path("streamId") streamId: String
    ): Call<StopStreamResponse>
    
    @GET("streams")
    fun listStreams(): Call<StreamListResponse>
}

data class StartStreamRequest(
    val device_id: String
)

data class StartStreamResponse(
    val success: Boolean,
    val streamId: String,
    val message: String,
    val websocket_url: String?
)

data class ChunkUploadResponse(
    val success: Boolean,
    val message: String
)

data class StopStreamResponse(
    val success: Boolean,
    val message: String
)

data class StreamListResponse(
    val success: Boolean,
    val streams: List<StreamInfo>,
    val total: Int
)

data class StreamInfo(
    val stream_id: String,
    val device_id: String,
    val is_active: Boolean,
    val created_at: String,
    val clients_count: Int,
    val buffer_size: Int
)