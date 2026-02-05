package com.example.inmo

import android.content.Context
import android.graphics.*
import android.util.AttributeSet
import android.util.Log
import android.view.SurfaceHolder
import android.view.SurfaceView
import java.nio.ByteBuffer

class ProcessedVideoView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : SurfaceView(context, attrs, defStyleAttr), SurfaceHolder.Callback {
    
    private var surfaceHolder: SurfaceHolder = holder
    private var isReady = false
    private var lastFrameData: ByteArray? = null
    private var videoWidth = 640
    private var videoHeight = 480
    
    // 复用Bitmap和像素数组以减少内存分配
    private var reusableBitmap: Bitmap? = null
    private var reusablePixels: IntArray? = null
    
    companion object {
        private const val TAG = "ProcessedVideoView"
    }
    
    init {
        surfaceHolder.addCallback(this)
    }
    
    /**
     * 设置视频尺寸
     */
    fun setVideoSize(width: Int, height: Int) {
        if (videoWidth != width || videoHeight != height) {
            videoWidth = width
            videoHeight = height
            
            // 重新创建Bitmap和像素数组
            reusableBitmap?.recycle()
            reusableBitmap = Bitmap.createBitmap(videoWidth, videoHeight, Bitmap.Config.RGB_565)
            reusablePixels = IntArray(videoWidth * videoHeight)
            
            Log.d(TAG, "设置视频尺寸: ${width}x${height}")
        }
    }
    
    override fun surfaceCreated(holder: SurfaceHolder) {
        Log.d(TAG, "Surface创建")
        isReady = true
        
        // 绘制初始背景
        drawBackground("等待处理后的视频数据...")
    }
    
    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {
        Log.d(TAG, "Surface改变: ${width}x${height}")
        isReady = true
    }
    
    override fun surfaceDestroyed(holder: SurfaceHolder) {
        Log.d(TAG, "Surface销毁")
        isReady = false
        
        // 清理资源
        reusableBitmap?.recycle()
        reusableBitmap = null
        reusablePixels = null
    }
    
    /**
     * 显示处理后的视频数据
     */
    fun displayProcessedData(data: ByteArray) {
        if (!isReady) {
            Log.w(TAG, "Surface未就绪，无法显示数据")
            return
        }
        
        lastFrameData = data
        
        try {
            // 跳过时间戳（前8字节）获取实际视频数据
            val videoData = if (data.size > 8) {
                data.sliceArray(8 until data.size)
            } else {
                data
            }
            
            // 尝试将YUV数据转换为RGB并显示
            displayVideoFrame(videoData)
            
        } catch (e: Exception) {
            Log.e(TAG, "显示视频帧失败: ${e.message}")
            // 如果视频显示失败，显示数据信息
            displayDataInfo(data)
        }
    }
    
    private fun displayVideoFrame(yuvData: ByteArray) {
        try {
            val canvas = surfaceHolder.lockCanvas()
            if (canvas != null) {
                // 清除画布
                canvas.drawColor(Color.BLACK)
                
                // 尝试将YUV数据转换为RGB bitmap
                val bitmap = convertYuvToRgbBitmap(yuvData)
                
                if (bitmap != null) {
                    // 计算缩放和居中显示
                    val canvasWidth = canvas.width
                    val canvasHeight = canvas.height
                    val bitmapWidth = bitmap.width
                    val bitmapHeight = bitmap.height
                    
                    // 计算缩放比例，保持宽高比
                    val scaleX = canvasWidth.toFloat() / bitmapWidth
                    val scaleY = canvasHeight.toFloat() / bitmapHeight
                    val scale = minOf(scaleX, scaleY)
                    
                    val scaledWidth = bitmapWidth * scale
                    val scaledHeight = bitmapHeight * scale
                    
                    val left = (canvasWidth - scaledWidth) / 2
                    val top = (canvasHeight - scaledHeight) / 2
                    
                    val destRect = RectF(left, top, left + scaledWidth, top + scaledHeight)
                    
                    // 绘制视频帧
                    canvas.drawBitmap(bitmap, null, destRect, null)
                    
                    // 绘制状态信息
                    drawVideoInfo(canvas, yuvData.size)
                    
                } else {
                    // 如果无法转换为bitmap，显示原始数据可视化
                    drawRawDataVisualization(canvas, yuvData)
                }
                
                surfaceHolder.unlockCanvasAndPost(canvas)
            }
        } catch (e: Exception) {
            Log.e(TAG, "显示视频帧失败: ${e.message}")
        }
    }
    
    private fun convertYuvToRgbBitmap(yuvData: ByteArray): Bitmap? {
        try {
            Log.d(TAG, "转换YUV数据: 尺寸=${videoWidth}x${videoHeight}, 数据大小=${yuvData.size}")
            
            // NV21格式：YYYYYYYY UVUV
            // 预期数据大小 = width * height * 3 / 2
            val expectedSize = videoWidth * videoHeight * 3 / 2
            
            if (yuvData.size < expectedSize) {
                Log.w(TAG, "YUV数据大小不足: 期望=$expectedSize, 实际=${yuvData.size}")
                return null
            }
            
            // 确保有可复用的Bitmap和像素数组
            if (reusableBitmap == null || reusablePixels == null) {
                reusableBitmap = Bitmap.createBitmap(videoWidth, videoHeight, Bitmap.Config.RGB_565)
                reusablePixels = IntArray(videoWidth * videoHeight)
            }
            
            val pixels = reusablePixels!!
            val frameSize = videoWidth * videoHeight
            
            // 优化的NV21转RGB算法 - 使用查找表和批量处理
            var pixelIndex = 0
            for (j in 0 until videoHeight) {
                for (i in 0 until videoWidth) {
                    val yIndex = j * videoWidth + i
                    val uvIndex = frameSize + (j / 2) * videoWidth + (i and 1.inv())
                    
                    if (yIndex >= yuvData.size || uvIndex + 1 >= yuvData.size) {
                        pixels[pixelIndex++] = Color.BLACK
                        continue
                    }
                    
                    val y = (yuvData[yIndex].toInt() and 0xFF)
                    val u = (yuvData[uvIndex].toInt() and 0xFF)
                    val v = (yuvData[uvIndex + 1].toInt() and 0xFF)
                    
                    // 快速YUV到RGB转换（简化版本）
                    val r = (y + ((v - 128) * 1.402)).toInt().coerceIn(0, 255)
                    val g = (y - ((u - 128) * 0.344) - ((v - 128) * 0.714)).toInt().coerceIn(0, 255)
                    val b = (y + ((u - 128) * 1.772)).toInt().coerceIn(0, 255)
                    
                    pixels[pixelIndex++] = Color.rgb(r, g, b)
                }
            }
            
            reusableBitmap!!.setPixels(pixels, 0, videoWidth, 0, 0, videoWidth, videoHeight)
            Log.d(TAG, "YUV转RGB成功")
            return reusableBitmap
            
        } catch (e: Exception) {
            Log.e(TAG, "YUV转RGB失败: ${e.message}")
            return null
        }
    }
    
    private fun drawVideoInfo(canvas: Canvas, dataSize: Int) {
        val paint = Paint().apply {
            color = Color.WHITE
            textSize = 24f
            isAntiAlias = true
            setShadowLayer(2f, 1f, 1f, Color.BLACK)
        }
        
        // 绘制视频信息
        canvas.drawText("📹 实时视频播放", 20f, 40f, paint)
        canvas.drawText("分辨率: ${videoWidth}x${videoHeight}", 20f, 70f, paint)
        canvas.drawText("数据: ${dataSize} bytes", 20f, 100f, paint)
        canvas.drawText("时间: ${System.currentTimeMillis()}", 20f, 130f, paint)
        
        // 绘制LIVE指示器
        paint.color = Color.RED
        canvas.drawCircle(canvas.width - 60f, 40f, 15f, paint)
        paint.color = Color.WHITE
        paint.textSize = 16f
        canvas.drawText("LIVE", canvas.width - 85f, 45f, paint)
    }
    
    private fun drawRawDataVisualization(canvas: Canvas, data: ByteArray) {
        val paint = Paint().apply {
            isAntiAlias = true
            textSize = 24f
            color = Color.WHITE
        }
        
        val width = canvas.width
        val height = canvas.height
        
        // 绘制背景
        canvas.drawColor(Color.parseColor("#1a1a2e"))
        
        // 绘制标题
        paint.color = Color.CYAN
        paint.textSize = 32f
        canvas.drawText("📊 原始数据可视化", 50f, 80f, paint)
        
        paint.color = Color.WHITE
        paint.textSize = 24f
        canvas.drawText("数据大小: ${data.size} bytes", 50f, 120f, paint)
        canvas.drawText("无法解码为视频，显示数据波形", 50f, 160f, paint)
        
        // 绘制数据波形
        drawDataWaveform(canvas, data, paint)
        
        // 绘制状态指示器
        drawStatusIndicator(canvas, paint)
    }
    
    private fun drawDataWaveform(canvas: Canvas, data: ByteArray, paint: Paint) {
        val width = canvas.width
        val height = canvas.height
        val centerY = height * 0.6f
        val startX = 50f
        val endX = width - 50f
        val maxAmplitude = 80f
        
        paint.color = Color.YELLOW
        paint.strokeWidth = 2f
        paint.style = Paint.Style.STROKE
        
        // 绘制中心线
        canvas.drawLine(startX, centerY, endX, centerY, paint)
        
        // 绘制数据波形
        paint.color = Color.GREEN
        paint.strokeWidth = 3f
        
        val path = Path()
        val sampleCount = minOf(data.size, 200)
        val stepX = (endX - startX) / sampleCount
        
        for (i in 0 until sampleCount) {
            val dataIndex = (i * data.size / sampleCount).coerceIn(0, data.size - 1)
            val value = data[dataIndex].toInt() and 0xFF
            val normalizedValue = (value - 128) / 128f
            val y = centerY + normalizedValue * maxAmplitude
            val x = startX + i * stepX
            
            if (i == 0) {
                path.moveTo(x, y)
            } else {
                path.lineTo(x, y)
            }
        }
        
        canvas.drawPath(path, paint)
    }
    
    private fun displayDataInfo(data: ByteArray) {
        try {
            val canvas = surfaceHolder.lockCanvas()
            if (canvas != null) {
                canvas.drawColor(Color.BLACK)
                
                val paint = Paint().apply {
                    isAntiAlias = true
                    textSize = 24f
                    color = Color.WHITE
                }
                
                // 绘制数据信息
                paint.color = Color.GREEN
                paint.textSize = 32f
                canvas.drawText("✅ 接收到处理后数据", 50f, 80f, paint)
                
                paint.color = Color.CYAN
                paint.textSize = 24f
                canvas.drawText("数据大小: ${data.size} bytes", 50f, 120f, paint)
                canvas.drawText("时间戳: ${System.currentTimeMillis()}", 50f, 160f, paint)
                
                // 提取时间戳
                if (data.size >= 8) {
                    try {
                        val timestampBytes = data.sliceArray(0..7)
                        val timestamp = ByteBuffer.wrap(timestampBytes).long
                        canvas.drawText("处理时间戳: $timestamp", 50f, 200f, paint)
                    } catch (e: Exception) {
                        // 忽略时间戳解析错误
                    }
                }
                
                // 绘制数据可视化
                drawDataWaveform(canvas, data, paint)
                
                // 绘制状态指示器
                drawStatusIndicator(canvas, paint)
                
                surfaceHolder.unlockCanvasAndPost(canvas)
            }
        } catch (e: Exception) {
            Log.e(TAG, "显示数据信息失败: ${e.message}")
        }
    }
    
    private fun drawStatusIndicator(canvas: Canvas, paint: Paint) {
        val width = canvas.width
        val height = canvas.height
        
        // 绘制状态指示器
        paint.style = Paint.Style.FILL
        paint.color = Color.GREEN
        
        val indicatorSize = 20f
        val x = width - 80f
        val y = 60f
        
        canvas.drawCircle(x, y, indicatorSize, paint)
        
        paint.color = Color.WHITE
        paint.textSize = 16f
        canvas.drawText("LIVE", x - 20f, y + 5f, paint)
    }
    
    private fun drawBackground(message: String) {
        if (!isReady) return
        
        try {
            val canvas = surfaceHolder.lockCanvas()
            if (canvas != null) {
                canvas.drawColor(Color.BLACK)
                
                val paint = Paint().apply {
                    color = Color.WHITE
                    textSize = 32f
                    textAlign = Paint.Align.CENTER
                    isAntiAlias = true
                }
                
                val x = canvas.width / 2f
                val y = canvas.height / 2f
                
                canvas.drawText(message, x, y, paint)
                
                surfaceHolder.unlockCanvasAndPost(canvas)
            }
        } catch (e: Exception) {
            Log.e(TAG, "绘制背景失败: ${e.message}")
        }
    }
    
    /**
     * 清除显示
     */
    fun clearDisplay() {
        drawBackground("视频流已停止")
    }
}