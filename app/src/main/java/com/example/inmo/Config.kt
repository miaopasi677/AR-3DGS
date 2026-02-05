package com.example.inmo

/**
 * 应用配置文件
 * 在这里修改服务器地址和其他配置参数
 * 
 * 注意：Android 9+ 默认不允许HTTP明文通信
 * 本应用已配置网络安全策略允许本地HTTP连接
 */
object Config {
    
    // 服务器配置
    // 请将此IP地址替换为你的服务器实际IP地址
    const val SERVER_IP = "192.168.2.19"
    const val SERVER_PORT = 5000
    
    // 协议配置 (开发环境使用HTTP，生产环境建议使用HTTPS)
    const val USE_HTTPS = false
    
    // 自动生成的URL
    val BASE_URL = if (USE_HTTPS) "https://$SERVER_IP:$SERVER_PORT/api/" else "http://$SERVER_IP:$SERVER_PORT/api/"
    val WEBSOCKET_URL = if (USE_HTTPS) "wss://$SERVER_IP:$SERVER_PORT" else "ws://$SERVER_IP:$SERVER_PORT"
    
    // 流传输配置
    const val FRAME_CAPTURE_INTERVAL = 200L // 帧捕获间隔(ms) - 5 FPS (降低帧率)
    const val CHUNK_SIZE = 8192 // 数据块大小 (8KB)
    
    // 视频配置
    const val MAX_VIDEO_WIDTH = 640 // 最大视频宽度
    const val MAX_VIDEO_HEIGHT = 480 // 最大视频高度
    
    // 网络配置
    const val CONNECT_TIMEOUT = 30L // 连接超时(秒)
    const val READ_TIMEOUT = 60L // 读取超时(秒)
    const val WRITE_TIMEOUT = 60L // 写入超时(秒)
    
    // 摄像头配置
    const val INMO_AIR3_RGB_CAMERA_ID = 0 // INMO AIR3 RGB摄像头ID
    
    // 调试配置
    const val DEBUG_MODE = true // 是否启用调试模式
    
    /**
     * 获取完整的服务器信息字符串
     */
    fun getServerInfo(): String {
        return "服务器: $SERVER_IP:$SERVER_PORT"
    }
    
    /**
     * 检查配置是否有效
     */
    fun isConfigValid(): Boolean {
        return SERVER_IP.isNotEmpty() && 
               SERVER_PORT > 0 && 
               SERVER_PORT < 65536
    }
}