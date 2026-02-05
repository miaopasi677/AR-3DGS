package com.example.inmo

import android.util.Log
import io.socket.client.IO
import io.socket.client.Socket
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.util.concurrent.atomic.AtomicBoolean

class StreamingManager(private val serverUrl: String) {
    
    private var socket: Socket? = null
    private var currentStreamId: String? = null
    private val isStreaming = AtomicBoolean(false)
    
    companion object {
        private const val TAG = "StreamingManager"
    }
    
    interface StreamingCallback {
        fun onStreamStarted(streamId: String)
        fun onStreamStopped()
        fun onChunkSent(success: Boolean)
        fun onProcessedData(data: ByteArray)
        fun onError(error: String)
    }
    
    private var callback: StreamingCallback? = null
    
    fun setCallback(callback: StreamingCallback) {
        this.callback = callback
    }
    
    fun startStream(deviceId: String) {
        if (isStreaming.get()) {
            Log.w(TAG, "流已经在运行中")
            return
        }
        
        val request = StartStreamRequest(deviceId)
        NetworkManager.videoApiService.startStream(request)
            .enqueue(object : Callback<StartStreamResponse> {
                override fun onResponse(
                    call: Call<StartStreamResponse>,
                    response: Response<StartStreamResponse>
                ) {
                    if (response.isSuccessful && response.body()?.success == true) {
                        val streamId = response.body()?.streamId
                        if (streamId != null) {
                            currentStreamId = streamId
                            isStreaming.set(true)
                            connectWebSocket(streamId)
                            callback?.onStreamStarted(streamId)
                            Log.d(TAG, "流开始成功: $streamId")
                        }
                    } else {
                        val error = "开始流失败: ${response.message()}"
                        Log.e(TAG, error)
                        callback?.onError(error)
                    }
                }
                
                override fun onFailure(call: Call<StartStreamResponse>, t: Throwable) {
                    val error = "网络错误: ${t.message}"
                    Log.e(TAG, error)
                    callback?.onError(error)
                }
            })
    }   
 
    fun sendChunk(data: ByteArray) {
        val streamId = currentStreamId
        if (!isStreaming.get() || streamId == null) {
            Log.w(TAG, "流未启动，无法发送数据")
            callback?.onChunkSent(false)
            return
        }
        
        val requestBody = data.toRequestBody("application/octet-stream".toMediaTypeOrNull())
        NetworkManager.videoApiService.uploadChunk(streamId, requestBody)
            .enqueue(object : Callback<ChunkUploadResponse> {
                override fun onResponse(
                    call: Call<ChunkUploadResponse>,
                    response: Response<ChunkUploadResponse>
                ) {
                    val success = response.isSuccessful && response.body()?.success == true
                    callback?.onChunkSent(success)
                    
                    if (!success) {
                        Log.w(TAG, "发送数据块失败: ${response.message()}")
                    }
                }
                
                override fun onFailure(call: Call<ChunkUploadResponse>, t: Throwable) {
                    Log.e(TAG, "发送数据块网络错误: ${t.message}")
                    callback?.onChunkSent(false)
                }
            })
    }
    
    fun stopStream() {
        val streamId = currentStreamId
        if (!isStreaming.get() || streamId == null) {
            Log.w(TAG, "流未启动")
            return
        }
        
        NetworkManager.videoApiService.stopStream(streamId)
            .enqueue(object : Callback<StopStreamResponse> {
                override fun onResponse(
                    call: Call<StopStreamResponse>,
                    response: Response<StopStreamResponse>
                ) {
                    cleanup()
                    callback?.onStreamStopped()
                    Log.d(TAG, "流停止成功")
                }
                
                override fun onFailure(call: Call<StopStreamResponse>, t: Throwable) {
                    Log.e(TAG, "停止流失败: ${t.message}")
                    cleanup()
                    callback?.onStreamStopped()
                }
            })
    }
    
    private fun connectWebSocket(streamId: String) {
        try {
            val options = IO.Options()
            options.forceNew = true
            options.reconnection = true
            
            socket = IO.socket(serverUrl, options)
            
            socket?.on(Socket.EVENT_CONNECT) {
                Log.d(TAG, "WebSocket连接成功")
                
                // 加入流房间
                val data = JSONObject()
                data.put("stream_id", streamId)
                socket?.emit("join_stream", data)
            }
            
            socket?.on(Socket.EVENT_DISCONNECT) {
                Log.d(TAG, "WebSocket断开连接")
            }
            
            socket?.on("joined_stream") { args ->
                Log.d(TAG, "成功加入流房间")
                
                // 请求处理后的数据流
                val data = JSONObject()
                data.put("stream_id", streamId)
                socket?.emit("request_processed_stream", data)
            }
            
            socket?.on("processed_stream_started") { args ->
                Log.d(TAG, "处理后数据流已启动")
            }
            
            socket?.on("processed_chunk") { args ->
                try {
                    if (args.isNotEmpty()) {
                        val data = args[0] as JSONObject
                        val base64Data = data.getString("data")
                        val decodedData = android.util.Base64.decode(base64Data, android.util.Base64.DEFAULT)
                        Log.d(TAG, "接收到处理后数据: ${decodedData.size} bytes")
                        callback?.onProcessedData(decodedData)
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "处理WebSocket数据失败: ${e.message}")
                }
            }
            
            socket?.on("error") { args ->
                val error = if (args.isNotEmpty()) args[0].toString() else "WebSocket错误"
                Log.e(TAG, "WebSocket错误: $error")
                callback?.onError(error)
            }
            
            socket?.connect()
            
        } catch (e: Exception) {
            Log.e(TAG, "WebSocket连接失败: ${e.message}")
            callback?.onError("WebSocket连接失败: ${e.message}")
        }
    }
    
    private fun cleanup() {
        isStreaming.set(false)
        currentStreamId = null
        
        socket?.disconnect()
        socket = null
    }
    
    fun isStreaming(): Boolean {
        return isStreaming.get()
    }
    
    fun getCurrentStreamId(): String? {
        return currentStreamId
    }
}