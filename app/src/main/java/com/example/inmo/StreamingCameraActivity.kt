package com.example.inmo

import android.Manifest
import android.app.AlertDialog
import android.content.pm.PackageManager
import android.graphics.ImageFormat
import android.hardware.Camera
import android.net.Uri
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.util.Log
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.view.View
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import android.widget.VideoView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.util.concurrent.atomic.AtomicBoolean

@Suppress("DEPRECATION")
class StreamingCameraActivity : AppCompatActivity(), SurfaceHolder.Callback {
    
    private var camera: Camera? = null
    private var surfaceView: SurfaceView? = null
    private var processedVideoView: ProcessedVideoView? = null
    private var surfaceHolder: SurfaceHolder? = null
    private var cameraStatusText: TextView? = null
    private var recordingStatusText: TextView? = null
    
    // UI控件
    private var btnStartStreaming: Button? = null
    private var btnStopStreaming: Button? = null
    private var btnPermissions: Button? = null
    private var btnSwitchView: Button? = null
    private var btnClose: Button? = null
    
    // INMO AIR3 RGB摄像头ID
    private var INMO_AIR3_RGB_CAMERA_ID = Config.INMO_AIR3_RGB_CAMERA_ID
    private var currentCameraId = 0
    private var isPreviewRunning = false
    private var isShowingProcessedVideo = false
    
    // 视频参数
    private var videoWidth = 640
    private var videoHeight = 480
    
    // 隐藏的Surface用于在切换视图时维持摄像头预览
    private var hiddenSurfaceView: SurfaceView? = null
    
    // 流传输管理器
    private var streamingManager: StreamingManager? = null
    private var isStreamingActive = AtomicBoolean(false)
    
    // 帧捕获
    private val handler = Handler(Looper.getMainLooper())
    private var frameCapture: Runnable? = null
    
    companion object {
        private const val TAG = "StreamingCameraActivity"
        private const val CAMERA_PERMISSION_REQUEST_CODE = 100
        private val FRAME_CAPTURE_INTERVAL = Config.FRAME_CAPTURE_INTERVAL
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_camera)
        
        // 初始化UI组件
        initViews()
        
        // 初始化SurfaceView
        surfaceView = findViewById(R.id.surfaceView)
        processedVideoView = findViewById(R.id.processedVideoView)
        
        // 确保ProcessedVideoView初始时是隐藏的
        processedVideoView?.visibility = View.GONE
        
        surfaceHolder = surfaceView?.holder
        surfaceHolder?.addCallback(this)
        
        // 初始化流管理器
        streamingManager = StreamingManager(Config.WEBSOCKET_URL)
        setupStreamingCallbacks()
        
        // 检查权限
        if (checkAllPermissions()) {
            initCamera()
        } else {
            requestAllPermissions()
        }
    }    
 
   private fun initViews() {
        cameraStatusText = findViewById(R.id.cameraStatus)
        recordingStatusText = findViewById(R.id.recordingStatus)
        
        btnStartStreaming = findViewById(R.id.btnStartRecording)
        btnStopStreaming = findViewById(R.id.btnStopRecording)
        btnPermissions = findViewById(R.id.btnPermissions)
        btnSwitchView = findViewById(R.id.btnSwitchView)
        btnClose = findViewById(R.id.btnClose)
        
        // 更新按钮文本
        btnStartStreaming?.text = "开始流传输"
        btnStopStreaming?.text = "停止流传输"
        
        // 开始流传输按钮
        btnStartStreaming?.setOnClickListener {
            startVideoStreaming()
        }
        
        // 停止流传输按钮
        btnStopStreaming?.setOnClickListener {
            stopVideoStreaming()
        }
        
        // 权限按钮
        btnPermissions?.setOnClickListener {
            showPermissionDialog()
        }
        
        // 切换视图按钮
        btnSwitchView?.setOnClickListener {
            switchView()
        }
        
        // 关闭按钮
        btnClose?.setOnClickListener {
            finish()
        }
        
        updateCameraStatus()
        updateStreamingStatus("待机")
        updateButtonStates()
        
        // 检查并显示权限状态
        checkPermissionStatus()
    }
    
    private fun updateCameraStatus() {
        cameraStatusText?.text = "摄像头ID: $currentCameraId | ${Config.getServerInfo()}"
    }
    
    private fun updateStreamingStatus(status: String) {
        recordingStatusText?.text = "状态: $status"
    }
    
    private fun setupStreamingCallbacks() {
        streamingManager?.setCallback(object : StreamingManager.StreamingCallback {
            override fun onStreamStarted(streamId: String) {
                runOnUiThread {
                    updateStreamingStatus("流传输中...")
                    updateButtonStates()
                    startFrameCapture()
                    Toast.makeText(this@StreamingCameraActivity, "流传输开始", Toast.LENGTH_SHORT).show()
                }
            }
            
            override fun onStreamStopped() {
                runOnUiThread {
                    updateStreamingStatus("流传输停止")
                    updateButtonStates()
                    stopFrameCapture()
                    processedVideoView?.clearDisplay()
                    Toast.makeText(this@StreamingCameraActivity, "流传输停止", Toast.LENGTH_SHORT).show()
                }
            }
            
            override fun onChunkSent(success: Boolean) {
                if (!success) {
                    Log.w(TAG, "数据块发送失败")
                } else {
                    Log.d(TAG, "数据块发送成功")
                }
            }
            
            override fun onProcessedData(data: ByteArray) {
                Log.d(TAG, "接收到处理后数据: ${data.size} bytes")
                runOnUiThread {
                    // 处理接收到的处理后数据
                    playProcessedData(data)
                }
            }
            
            override fun onError(error: String) {
                runOnUiThread {
                    updateStreamingStatus("错误: $error")
                    Toast.makeText(this@StreamingCameraActivity, "流传输错误: $error", Toast.LENGTH_SHORT).show()
                }
            }
        })
    }   
 
    private fun startVideoStreaming() {
        if (isStreamingActive.get()) {
            Log.d(TAG, "流传输已在运行中")
            return
        }
        
        if (!isPreviewRunning) {
            Toast.makeText(this, "摄像头预览未就绪", Toast.LENGTH_SHORT).show()
            return
        }
        
        // 检查录音权限
        if (!checkAudioPermission()) {
            Toast.makeText(this, "需要录音权限才能进行流传输", Toast.LENGTH_SHORT).show()
            requestAllPermissions()
            return
        }
        
        val deviceId = "INMO_AIR3_${android.os.Build.SERIAL}"
        streamingManager?.startStream(deviceId)
        isStreamingActive.set(true)
    }
    
    private fun stopVideoStreaming() {
        if (!isStreamingActive.get()) {
            Log.d(TAG, "流传输未运行")
            return
        }
        
        streamingManager?.stopStream()
        isStreamingActive.set(false)
        stopFrameCapture()
    }
    
    private fun startFrameCapture() {
        frameCapture = object : Runnable {
            override fun run() {
                if (isStreamingActive.get() && isPreviewRunning) {
                    captureFrame()
                    handler.postDelayed(this, FRAME_CAPTURE_INTERVAL)
                }
            }
        }
        handler.post(frameCapture!!)
    }
    
    private fun stopFrameCapture() {
        frameCapture?.let { handler.removeCallbacks(it) }
        frameCapture = null
    }
    
    private fun captureFrame() {
        camera?.let { cam ->
            try {
                // 使用PreviewCallback捕获帧数据
                cam.setOneShotPreviewCallback { data, camera ->
                    if (data != null && isStreamingActive.get()) {
                        Log.d(TAG, "捕获帧数据: ${data.size} bytes")
                        // 将YUV数据转换为字节数组并发送
                        streamingManager?.sendChunk(data)
                    } else {
                        Log.w(TAG, "帧数据为空或流未激活")
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "捕获帧失败: ${e.message}")
            }
        }
    }
    
    private fun playProcessedData(data: ByteArray) {
        Log.d(TAG, "接收到处理后的数据: ${data.size} bytes")
        
        // 使用自定义视图显示处理后的数据，传递实际的视频尺寸
        processedVideoView?.setVideoSize(videoWidth, videoHeight)
        processedVideoView?.displayProcessedData(data)
        
        // 自动切换到处理后的视频视图
        if (!isShowingProcessedVideo) {
            switchView()
        }
    }
    
    private fun switchView() {
        isShowingProcessedVideo = !isShowingProcessedVideo
        
        if (isShowingProcessedVideo) {
            // 显示处理后的视频（放到前面）
            processedVideoView?.bringToFront()
            processedVideoView?.visibility = View.VISIBLE
            btnSwitchView?.text = "显示摄像头"
            
            Log.d(TAG, "切换到处理后视频视图，摄像头预览在后台继续运行")
        } else {
            // 显示摄像头预览（放到前面）
            surfaceView?.bringToFront()
            processedVideoView?.visibility = View.GONE
            btnSwitchView?.text = "显示处理后视频"
            
            Log.d(TAG, "切换到摄像头预览视图")
        }
    }
    
    private fun updateButtonStates() {
        val streaming = isStreamingActive.get()
        btnStartStreaming?.isEnabled = !streaming
        btnStopStreaming?.isEnabled = streaming
    }  
  
    // 权限相关方法
    private fun checkAllPermissions(): Boolean {
        return checkCameraPermission()
    }
    
    private fun requestAllPermissions() {
        val permissions = mutableListOf<String>()
        
        if (!checkCameraPermission()) {
            permissions.add(Manifest.permission.CAMERA)
        }
        
        if (android.os.Build.VERSION.SDK_INT <= android.os.Build.VERSION_CODES.P) {
            if (!checkStoragePermission()) {
                permissions.add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
                permissions.add(Manifest.permission.READ_EXTERNAL_STORAGE)
            }
        }
        
        if (!checkAudioPermission()) {
            permissions.add(Manifest.permission.RECORD_AUDIO)
        }
        
        if (permissions.isNotEmpty()) {
            ActivityCompat.requestPermissions(
                this,
                permissions.toTypedArray(),
                CAMERA_PERMISSION_REQUEST_CODE
            )
        }
    }
    
    private fun checkCameraPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.CAMERA
        ) == PackageManager.PERMISSION_GRANTED
    }
    
    private fun checkStoragePermission(): Boolean {
        return if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.Q) {
            true
        } else {
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.WRITE_EXTERNAL_STORAGE
            ) == PackageManager.PERMISSION_GRANTED
        }
    }
    
    private fun checkAudioPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED
    }
    
    private fun checkPermissionStatus() {
        val permissions = mutableListOf<String>()
        
        if (!checkCameraPermission()) {
            permissions.add("摄像头")
        }
        
        if (android.os.Build.VERSION.SDK_INT <= android.os.Build.VERSION_CODES.P) {
            if (!checkStoragePermission()) {
                permissions.add("存储")
            }
        }
        
        if (!checkAudioPermission()) {
            permissions.add("录音")
        }
        
        if (permissions.isNotEmpty()) {
            val message = "缺少权限: ${permissions.joinToString("、")}"
            updateStreamingStatus(message)
        } else {
            updateStreamingStatus("权限就绪")
        }
    }
    
    private fun showPermissionDialog() {
        val message = buildString {
            append("应用需要以下权限才能正常工作：\n\n")
            append("📷 摄像头权限：用于实时视频流\n")
            append("🎤 录音权限：用于音频流传输\n")
            
            if (android.os.Build.VERSION.SDK_INT <= android.os.Build.VERSION_CODES.P) {
                append("💾 存储权限：用于临时文件\n")
            }
            
            append("\n是否现在授予权限？")
        }
        
        AlertDialog.Builder(this)
            .setTitle("权限说明")
            .setMessage(message)
            .setPositiveButton("授予权限") { _, _ ->
                requestAllPermissions()
            }
            .setNegativeButton("取消", null)
            .show()
    }    
 
   override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        when (requestCode) {
            CAMERA_PERMISSION_REQUEST_CODE -> {
                var cameraGranted = false
                var storageGranted = false
                var audioGranted = false
                
                for (i in permissions.indices) {
                    when (permissions[i]) {
                        Manifest.permission.CAMERA -> {
                            cameraGranted = grantResults[i] == PackageManager.PERMISSION_GRANTED
                        }
                        Manifest.permission.WRITE_EXTERNAL_STORAGE,
                        Manifest.permission.READ_EXTERNAL_STORAGE -> {
                            if (grantResults[i] == PackageManager.PERMISSION_GRANTED) {
                                storageGranted = true
                            }
                        }
                        Manifest.permission.RECORD_AUDIO -> {
                            audioGranted = grantResults[i] == PackageManager.PERMISSION_GRANTED
                        }
                    }
                }
                
                if (cameraGranted) {
                    initCamera()
                    
                    val missingPermissions = mutableListOf<String>()
                    
                    if (android.os.Build.VERSION.SDK_INT <= android.os.Build.VERSION_CODES.P && !storageGranted) {
                        missingPermissions.add("存储")
                    }
                    if (!audioGranted) {
                        missingPermissions.add("录音")
                    }
                    
                    if (missingPermissions.isNotEmpty()) {
                        val message = "缺少${missingPermissions.joinToString("、")}权限，部分功能可能受限"
                        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
                        updateStreamingStatus("权限受限")
                    } else {
                        updateStreamingStatus("权限就绪")
                    }
                } else {
                    Toast.makeText(this, "摄像头权限是必需的，无法继续使用", Toast.LENGTH_SHORT).show()
                    finish()
                }
            }
        }
    }
    
    // 摄像头相关方法
    private fun initCamera() {
        try {
            if (!CameraHelper.isCameraAvailable(INMO_AIR3_RGB_CAMERA_ID)) {
                Toast.makeText(this, "摄像头 $INMO_AIR3_RGB_CAMERA_ID 不可用", Toast.LENGTH_SHORT).show()
                finish()
                return
            }
            
            camera = Camera.open(INMO_AIR3_RGB_CAMERA_ID)
            currentCameraId = INMO_AIR3_RGB_CAMERA_ID
            updateCameraStatus()
            
            camera?.let { CameraHelper.logCameraCapabilities(it) }
            
            Log.d(TAG, "摄像头打开成功，ID: $INMO_AIR3_RGB_CAMERA_ID")
            Log.d(TAG, "系统总摄像头数量: ${CameraHelper.getNumberOfCameras()}")
            
        } catch (e: Exception) {
            Log.e(TAG, "打开摄像头失败: ${e.message}")
            Toast.makeText(this, "打开摄像头失败: ${e.message}", Toast.LENGTH_SHORT).show()
            finish()
        }
    }
    
    override fun surfaceCreated(holder: SurfaceHolder) {
        Log.d(TAG, "Surface创建")
        startCameraPreview()
    }
    
    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {
        Log.d(TAG, "Surface改变: ${width}x${height}")
        stopCameraPreview()
        startCameraPreview()
    }
    
    override fun surfaceDestroyed(holder: SurfaceHolder) {
        Log.d(TAG, "Surface销毁")
        stopCameraPreview()
    }
    
    private fun startCameraPreview() {
        camera?.let { cam ->
            try {
                cam.setPreviewDisplay(surfaceHolder)
                
                val parameters = cam.parameters
                val supportedPreviewSizes = parameters.supportedPreviewSizes
                
                if (supportedPreviewSizes.isNotEmpty()) {
                    // 选择合适的分辨率（不超过640x480）
                    val targetSize = findBestPreviewSize(supportedPreviewSizes, Config.MAX_VIDEO_WIDTH, Config.MAX_VIDEO_HEIGHT)
                    parameters.setPreviewSize(targetSize.width, targetSize.height)
                    
                    // 保存实际的预览尺寸
                    videoWidth = targetSize.width
                    videoHeight = targetSize.height
                    
                    Log.d(TAG, "设置预览尺寸: ${targetSize.width}x${targetSize.height}")
                    
                    // 设置预览格式为NV21（YUV420SP）
                    parameters.previewFormat = ImageFormat.NV21
                    Log.d(TAG, "设置预览格式: NV21")
                }
                
                val focusModes = parameters.supportedFocusModes
                if (focusModes.contains(Camera.Parameters.FOCUS_MODE_CONTINUOUS_VIDEO)) {
                    parameters.focusMode = Camera.Parameters.FOCUS_MODE_CONTINUOUS_VIDEO
                    Log.d(TAG, "设置连续视频对焦模式")
                } else if (focusModes.contains(Camera.Parameters.FOCUS_MODE_AUTO)) {
                    parameters.focusMode = Camera.Parameters.FOCUS_MODE_AUTO
                    Log.d(TAG, "设置自动对焦")
                }
                
                cam.parameters = parameters
                cam.startPreview()
                isPreviewRunning = true
                Log.d(TAG, "摄像头预览开始")
                
            } catch (e: IOException) {
                Log.e(TAG, "设置摄像头预览失败: ${e.message}")
                Toast.makeText(this, "摄像头预览失败", Toast.LENGTH_SHORT).show()
                isPreviewRunning = false
            } catch (e: Exception) {
                Log.e(TAG, "摄像头预览异常: ${e.message}")
                Toast.makeText(this, "摄像头预览异常", Toast.LENGTH_SHORT).show()
                isPreviewRunning = false
            }
        }
    }
    
    private fun findBestPreviewSize(sizes: List<Camera.Size>, maxWidth: Int, maxHeight: Int): Camera.Size {
        // 找到最接近目标分辨率且不超过最大限制的尺寸
        var bestSize = sizes[0]
        var bestScore = Int.MAX_VALUE
        
        for (size in sizes) {
            // 跳过过大的分辨率
            if (size.width > maxWidth || size.height > maxHeight) {
                continue
            }
            
            // 计算与目标分辨率的差距
            val score = Math.abs(size.width - maxWidth) + Math.abs(size.height - maxHeight)
            if (score < bestScore) {
                bestScore = score
                bestSize = size
            }
        }
        
        Log.d(TAG, "选择的预览尺寸: ${bestSize.width}x${bestSize.height}")
        return bestSize
    }
    
    private fun stopCameraPreview() {
        camera?.let { cam ->
            try {
                if (isPreviewRunning) {
                    cam.stopPreview()
                    isPreviewRunning = false
                    Log.d(TAG, "摄像头预览停止")
                } else {
                    Log.d(TAG, "预览已经停止")
                }
            } catch (e: Exception) {
                Log.e(TAG, "停止摄像头预览失败: ${e.message}")
            }
        }
    }
    
    override fun onPause() {
        super.onPause()
        stopVideoStreaming()
        releaseCamera()
    }
    
    override fun onDestroy() {
        super.onDestroy()
        stopVideoStreaming()
        releaseCamera()
    }
    
    private fun releaseCamera() {
        camera?.let { cam ->
            try {
                if (isPreviewRunning) {
                    cam.stopPreview()
                    isPreviewRunning = false
                }
                cam.release()
                camera = null
                Log.d(TAG, "摄像头资源释放")
            } catch (e: Exception) {
                Log.e(TAG, "释放摄像头资源失败: ${e.message}")
            }
        }
    }
}