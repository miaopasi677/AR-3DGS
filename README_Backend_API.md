# INMO AIR3 视频处理后台API说明

## 概述
这个应用需要一个后台服务器来处理上传的视频并返回处理后的视频。

## API接口

### 1. 上传视频
```
POST /api/upload/video
Content-Type: multipart/form-data

参数:
- video: 视频文件 (multipart file)
- device_id: 设备ID (string)

响应:
{
  "success": true,
  "videoId": "unique_video_id",
  "message": "视频上传成功"
}
```

### 2. 检查视频处理状态
```
GET /api/video/{videoId}/status

响应:
{
  "success": true,
  "status": "processing|completed|failed",
  "processedVideoUrl": "https://your-server.com/processed/video.mp4",
  "message": "处理状态信息"
}
```

### 3. 获取处理后的视频
```
GET /api/video/{videoId}

响应: 视频文件流
```

## 配置说明

在 `NetworkManager.kt` 中修改 `BASE_URL` 为你的服务器地址：

```kotlin
private const val BASE_URL = "https://your-backend-server.com/api/"
```

## 示例后台实现 (Node.js + Express)

```javascript
const express = require('express');
const multer = require('multer');
const app = express();

// 配置文件上传
const upload = multer({ dest: 'uploads/' });

// 上传视频
app.post('/api/upload/video', upload.single('video'), (req, res) => {
  const videoId = generateUniqueId();
  
  // 这里添加你的视频处理逻辑
  processVideo(req.file.path, videoId);
  
  res.json({
    success: true,
    videoId: videoId,
    message: '视频上传成功'
  });
});

// 检查处理状态
app.get('/api/video/:videoId/status', (req, res) => {
  const status = getProcessingStatus(req.params.videoId);
  
  res.json({
    success: true,
    status: status.status,
    processedVideoUrl: status.url,
    message: status.message
  });
});

// 获取处理后的视频
app.get('/api/video/:videoId', (req, res) => {
  const videoPath = getProcessedVideoPath(req.params.videoId);
  res.sendFile(videoPath);
});

app.listen(3000, () => {
  console.log('服务器运行在端口 3000');
});
```

## 视频处理建议

1. **实时处理**: 使用FFmpeg或类似工具进行视频处理
2. **异步处理**: 使用队列系统(如Redis Queue)处理视频
3. **存储**: 使用云存储(AWS S3, 阿里云OSS等)存储视频文件
4. **CDN**: 使用CDN加速视频播放

## 安全考虑

1. 添加API认证
2. 限制文件大小和格式
3. 验证设备ID
4. 添加速率限制