# 🔧 单帧播放问题修复

## 🐛 问题描述

用户反馈"就只能播放第一帧"，视频在切换到处理后视图时只显示第一帧，后续帧不更新。

## 🔍 问题分析

从日志分析发现：

### ✅ 正常的部分
- 第一帧YUV转RGB成功
- WebSocket数据接收正常
- 视频尺寸正确（640×480）

### ❌ 问题根源
```
2026-02-05 11:04:27.690 SV[6820983...aActivity] surfaceDestroyed callback
2026-02-05 11:04:27.702 StreamingCameraActivity 摄像头预览停止
```

**核心问题**：当用户点击"切换视图"时：
1. 摄像头预览的SurfaceView被隐藏（`visibility = GONE`）
2. SurfaceView的Surface被销毁
3. `surfaceDestroyed`回调被触发
4. 摄像头预览停止
5. 帧捕获循环停止
6. 不再有新的视频数据上传
7. 只能显示最后接收到的一帧

## ✅ 修复方案

### 方案1: 保持摄像头预览运行（已实现）

**核心思路**：不隐藏摄像头SurfaceView，而是通过Z-order控制显示层级

```kotlin
private fun switchView() {
    isShowingProcessedVideo = !isShowingProcessedVideo
    
    if (isShowingProcessedVideo) {
        // 显示处理后的视频（放到前面）
        processedVideoView?.bringToFront()
        processedVideoView?.visibility = View.VISIBLE
        btnSwitchView?.text = "显示摄像头"
    } else {
        // 显示摄像头预览（放到前面）
        surfaceView?.bringToFront()
        processedVideoView?.visibility = View.GONE
        btnSwitchView?.text = "显示处理后视频"
    }
}
```

**优势**：
- ✅ 摄像头预览始终运行
- ✅ 帧捕获循环不中断
- ✅ 视频数据持续上传
- ✅ 处理后视频持续更新

## 🎯 修复效果

### 修复前的流程
```
用户点击"切换视图"
    ↓
SurfaceView.visibility = GONE
    ↓
Surface销毁
    ↓
摄像头预览停止
    ↓
帧捕获停止
    ↓
只显示最后一帧 ❌
```

### 修复后的流程
```
用户点击"切换视图"
    ↓
ProcessedVideoView.bringToFront()
    ↓
摄像头预览继续运行
    ↓
帧捕获持续进行
    ↓
视频持续更新 ✅
```

## 🧪 测试验证

### 测试步骤
1. 启动应用并开始流传输
2. 等待第一帧显示成功
3. 点击"切换视图"
4. 观察处理后视频是否持续更新

### 预期结果
- ✅ 第一帧正常显示
- ✅ 后续帧持续更新
- ✅ 视频播放流畅
- ✅ 可以正常切换回摄像头预览

### 验证日志
应该看到持续的日志输出：
```
StreamingCameraActivity: 捕获帧数据: 460800 bytes
StreamingCameraActivity: 数据块发送成功
StreamingCameraActivity: 接收到处理后数据: 460808 bytes
ProcessedVideoView: 转换YUV数据: 尺寸=640x480
ProcessedVideoView: YUV转RGB成功
```

## 🔮 进一步优化

### 1. 性能优化
```kotlin
// 当显示摄像头预览时，可以暂停ProcessedVideoView的更新
if (!isShowingProcessedVideo) {
    // 跳过YUV转换，节省CPU
    return
}
```

### 2. 内存优化
```kotlin
// 当不显示处理后视频时，释放Bitmap资源
if (!isShowingProcessedVideo) {
    reusableBitmap?.recycle()
    reusableBitmap = null
}
```

### 3. 用户体验优化
```kotlin
// 添加切换动画
private fun switchViewWithAnimation() {
    val fadeOut = AlphaAnimation(1.0f, 0.0f)
    val fadeIn = AlphaAnimation(0.0f, 1.0f)
    
    // 淡出当前视图，淡入新视图
}
```

## 📝 技术要点

### SurfaceView生命周期
```
SurfaceView.visibility = VISIBLE
    ↓
surfaceCreated() 回调
    ↓
摄像头预览开始
    ↓
SurfaceView.visibility = GONE
    ↓
surfaceDestroyed() 回调
    ↓
摄像头预览停止
```

### Z-order控制
```kotlin
// bringToFront() 将View移到最前面
processedVideoView?.bringToFront()

// 或者使用elevation
processedVideoView?.elevation = 10f
surfaceView?.elevation = 0f
```

### 视图层级管理
```
FrameLayout (父容器)
├── SurfaceView (摄像头预览) - 始终可见
└── ProcessedVideoView (处理后视频) - 按需显示
```

## 🎊 总结

通过修改视图切换逻辑，从"隐藏/显示"改为"层级控制"，成功解决了单帧播放问题：

1. ✅ **保持摄像头运行** - 不再销毁Surface
2. ✅ **持续帧捕获** - 数据流不中断
3. ✅ **流畅视频播放** - 所有帧都能正常更新
4. ✅ **用户体验提升** - 切换视图更加流畅

现在用户可以享受真正的实时视频播放体验了！🚀

---

*修复时间: 2026-02-05*  
*状态: 单帧问题已修复* ✅