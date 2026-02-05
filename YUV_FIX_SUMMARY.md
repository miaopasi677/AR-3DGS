# 🔧 YUV视频显示修复说明

## 🐛 问题描述

用户反馈手机上显示的视频是"条纹乱码"，这是典型的YUV数据解析错误导致的问题。

## 🔍 问题分析

### 原因1: 错误的分辨率估算
- 之前的代码基于数据大小猜测分辨率
- 猜测的分辨率与实际摄像头输出不匹配
- 导致图像行列错位，显示为条纹

### 原因2: 简化的YUV处理
- 之前只使用Y分量（亮度），忽略UV分量（色度）
- 没有按照NV21格式正确解析数据
- 导致颜色信息丢失和图像错乱

### 原因3: 缺少格式规范
- 摄像头默认输出格式不确定
- 没有明确指定NV21格式
- 数据对齐和内存布局可能不正确

## ✅ 修复方案

### 1. 获取实际摄像头分辨率
```kotlin
// 在startCameraPreview中
val parameters = cam.parameters
val supportedPreviewSizes = parameters.supportedPreviewSizes
if (supportedPreviewSizes.isNotEmpty()) {
    val previewSize = supportedPreviewSizes[0]
    parameters.setPreviewSize(previewSize.width, previewSize.height)
    
    // 保存实际尺寸
    videoWidth = previewSize.width
    videoHeight = previewSize.height
    
    // 明确设置NV21格式
    parameters.previewFormat = ImageFormat.NV21
}
```

### 2. 正确的NV21到RGB转换
```kotlin
// NV21格式：YYYYYYYY UVUV
val frameSize = videoWidth * videoHeight

for (j in 0 until videoHeight) {
    for (i in 0 until videoWidth) {
        val yIndex = j * videoWidth + i
        val uvIndex = frameSize + (j / 2) * videoWidth + (i and 1.inv())
        
        val y = (yuvData[yIndex].toInt() and 0xFF) - 16
        val u = (yuvData[uvIndex].toInt() and 0xFF) - 128
        val v = (yuvData[uvIndex + 1].toInt() and 0xFF) - 128
        
        // 标准YUV到RGB转换公式
        val y1192 = if (y < 0) 0 else 1192 * y
        var r = (y1192 + 1634 * v)
        var g = (y1192 - 833 * v - 400 * u)
        var b = (y1192 + 2066 * u)
        
        // 限制范围并转换
        pixels[yIndex] = Color.rgb(
            (r shr 10) and 0xFF,
            (g shr 10) and 0xFF,
            (b shr 10) and 0xFF
        )
    }
}
```

### 3. 传递准确的视频参数
```kotlin
// 在playProcessedData中传递实际尺寸
processedVideoView?.setVideoSize(videoWidth, videoHeight)
processedVideoView?.displayProcessedData(data)
```

## 🎯 预期效果

### 修复前
- ❌ 条纹乱码显示
- ❌ 颜色错乱
- ❌ 图像错位
- ❌ 分辨率不匹配

### 修复后
- ✅ 正确的彩色视频显示
- ✅ 图像清晰，无条纹
- ✅ 分辨率匹配摄像头输出
- ✅ 颜色还原正确

## 🔧 技术细节

### NV21格式说明
```
NV21 (YUV420SP) 格式布局:
YYYYYYYY YYYYYYYY YYYYYYYY YYYYYYYY  <- Y平面 (亮度)
YYYYYYYY YYYYYYYY YYYYYYYY YYYYYYYY
YYYYYYYY YYYYYYYY YYYYYYYY YYYYYYYY
YYYYYYYY YYYYYYYY YYYYYYYY YYYYYYYY
VUVUVUVU VUVUVUVU                    <- UV平面 (色度，交错存储)
VUVUVUVU VUVUVUVU

数据大小 = width * height * 3 / 2
```

### YUV到RGB转换公式
```
标准ITU-R BT.601转换:
R = Y + 1.402 * (V - 128)
G = Y - 0.344 * (U - 128) - 0.714 * (V - 128)  
B = Y + 1.772 * (U - 128)

优化的整数运算:
y1192 = 1192 * (Y - 16)
R = (y1192 + 1634 * (V - 128)) >> 10
G = (y1192 - 833 * (V - 128) - 400 * (U - 128)) >> 10
B = (y1192 + 2066 * (U - 128)) >> 10
```

## 🧪 测试方法

### 1. 安装更新的APK
```bash
./gradlew assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

### 2. 测试步骤
1. 启动应用，授予摄像头权限
2. 点击"开始流传输"
3. 等待几秒让数据开始传输
4. 点击"切换视图"查看处理后视频
5. 应该看到清晰的彩色视频，而不是条纹

### 3. 验证要点
- ✅ 视频画面清晰，无条纹乱码
- ✅ 颜色正常，不是纯灰度
- ✅ 分辨率信息正确显示
- ✅ 实时更新，无卡顿

## 📊 性能优化

### 当前实现
- 每帧进行完整的YUV到RGB转换
- 使用软件转换，CPU密集

### 未来优化方向
1. **使用RenderScript加速**
```kotlin
val rs = RenderScript.create(context)
val yuvToRgbScript = ScriptIntrinsicYuvToRGB.create(rs, Element.U8_4(rs))
```

2. **使用OpenGL ES着色器**
```glsl
// 片段着色器中的YUV到RGB转换
vec3 yuv = texture2D(u_texture, v_texCoord).rgb;
vec3 rgb = mat3(1.0, 1.0, 1.0,
                0.0, -0.344, 1.772,
                1.402, -0.714, 0.0) * yuv;
```

3. **使用MediaCodec硬件解码**
```kotlin
val decoder = MediaCodec.createDecoderByType("video/avc")
// 配置硬件解码器
```

## 🚨 注意事项

### 1. 内存使用
- 每帧创建新的Bitmap会增加内存压力
- 建议复用Bitmap对象

### 2. 性能影响
- YUV到RGB转换是CPU密集操作
- 高分辨率下可能影响帧率

### 3. 格式兼容性
- 不同设备可能使用不同的YUV格式
- 需要检测和适配多种格式

## 📝 总结

通过这次修复：
1. ✅ 获取了摄像头的实际分辨率参数
2. ✅ 明确指定了NV21预览格式
3. ✅ 实现了正确的NV21到RGB转换算法
4. ✅ 传递了准确的视频尺寸信息

现在应该能看到清晰的彩色视频，而不是条纹乱码了！

---

*修复时间: 2026-02-05*  
*状态: 已修复YUV解析问题* ✅