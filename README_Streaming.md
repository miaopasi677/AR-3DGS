# INMO AIR3 实时视频流传输系统

## 🎯 系统概述

这是一个完整的实时视频流传输系统，支持INMO AIR3设备的摄像头数据实时上传、处理和播放。

### 🏗️ 系统架构

```
INMO AIR3设备 → Android应用 → Flask后端 → 实时处理 → 返回给Android应用
     ↓              ↓           ↓           ↓              ↓
  摄像头数据    → 数据块上传 → WebSocket → 视频处理 → 处理后数据播放
```

## 🚀 快速开始

### 1. 启动后端服务器

```bash
cd backend
python start_streaming_server.py
```

服务器启动后会显示：
- 本地访问地址
- 网络访问地址  
- WebSocket地址
- API接口列表

### 2. 配置Android应用

在 `StreamingManager.kt` 中修改服务器地址：

```kotlin
streamingManager = StreamingManager("http://YOUR_SERVER_IP:5000")
```

### 3. 运行Android应用

1. 安装APK到INMO AIR3设备
2. 授予摄像头和录音权限
3. 点击"开始流传输"
4. 实时视频数据将被上传并处理

## 📡 API接口

### 开始流传输
```http
POST /api/stream/start
Content-Type: application/json

{
  "device_id": "INMO_AIR3_device_123"
}
```

### 上传数据块
```http
POST /api/stream/{streamId}/chunk
Content-Type: application/octet-stream

[二进制视频数据]
```

### 获取处理后的流
```http
GET /api/stream/{streamId}
```

### 停止流传输
```http
POST /api/stream/{streamId}/stop
```

### 获取流列表
```http
GET /api/streams
```

## 🔌 WebSocket事件

### 客户端发送事件

- `join_stream`: 加入视频流房间
- `leave_stream`: 离开视频流房间  
- `get_processed_chunk`: 请求处理后的数据块

### 服务器发送事件

- `connected`: 连接成功
- `joined_stream`: 成功加入流
- `new_chunk`: 新数据块通知
- `processed_chunk`: 处理后的数据块
- `stream_stopped`: 流已停止
- `error`: 错误信息

## 🎥 Android应用功能

### 主要功能
- ✅ 实时摄像头预览
- ✅ 实时数据流上传
- ✅ WebSocket双向通信
- ✅ 处理后数据接收
- ✅ 权限智能管理
- ✅ 错误处理和重连

### 界面控制
- **开始流传输**: 开始实时视频流
- **停止流传输**: 停止视频流
- **权限**: 管理应用权限
- **切换视图**: 在摄像头预览和处理后视频间切换
- **关闭**: 退出应用

## 🔧 技术特性

### 后端特性
- **实时处理**: 边接收边处理视频数据
- **WebSocket支持**: 双向实时通信
- **多客户端**: 支持多个设备同时连接
- **缓冲管理**: 智能缓冲区管理防止内存溢出
- **错误恢复**: 完善的错误处理和恢复机制

### Android特性
- **实时捕获**: 10FPS实时帧捕获
- **数据压缩**: 智能数据压缩减少带宽
- **权限适配**: 适配不同Android版本权限
- **网络优化**: 网络状态检测和重连
- **UI响应**: 流畅的用户界面

## 🧪 测试工具

### 测试API
```bash
cd backend
python test_streaming.py
```

### 测试内容
- ✅ 服务器状态检查
- ✅ 流创建和管理
- ✅ 数据块上传
- ✅ WebSocket通信
- ✅ 流列表获取
- ✅ 流停止功能

## 📊 性能参数

### 默认配置
- **帧率**: 10 FPS
- **数据块大小**: 8KB
- **缓冲区大小**: 100个数据块
- **处理延迟**: ~100ms
- **网络超时**: 60秒

### 可调参数
```python
# 后端配置 (streaming_app.py)
CHUNK_SIZE = 8192          # 数据块大小
MAX_BUFFER_SIZE = 100      # 最大缓冲区

# Android配置 (StreamingCameraActivity.kt)
FRAME_CAPTURE_INTERVAL = 100L  # 帧捕获间隔(ms)
```

## 🔒 安全考虑

1. **网络安全**: 建议在生产环境中使用HTTPS
2. **权限控制**: 实现设备认证和权限验证
3. **数据加密**: 对敏感视频数据进行加密
4. **速率限制**: 防止恶意客户端攻击

## 🐛 故障排除

### 常见问题

**Q: 连接服务器失败**
A: 检查服务器IP地址和端口，确保防火墙允许访问

**Q: 权限被拒绝**  
A: 在Android设置中手动授予摄像头和录音权限

**Q: 视频卡顿**
A: 检查网络连接，降低帧率或数据块大小

**Q: 内存不足**
A: 减少缓冲区大小，优化数据处理逻辑

### 日志查看
- **Android**: 使用 `adb logcat | grep StreamingCamera`
- **后端**: 服务器控制台直接显示日志

## 🔄 版本历史

- **v2.0.0**: 实时流传输架构
- **v1.0.0**: 基础视频上传功能

## 📞 技术支持

如有问题请检查：
1. 网络连接状态
2. 服务器运行状态  
3. 权限授予情况
4. 日志错误信息

---

🎉 **享受实时视频流传输体验！**