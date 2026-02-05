package com.example.inmo

import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object NetworkManager {
    
    // 使用配置文件中的服务器地址
    private val BASE_URL = Config.BASE_URL
    
    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(Config.CONNECT_TIMEOUT, TimeUnit.SECONDS)
        .readTimeout(Config.READ_TIMEOUT, TimeUnit.SECONDS)
        .writeTimeout(Config.WRITE_TIMEOUT, TimeUnit.SECONDS)
        .build()
    
    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val videoApiService: VideoApiService = retrofit.create(VideoApiService::class.java)
}