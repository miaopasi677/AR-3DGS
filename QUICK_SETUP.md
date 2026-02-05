# 🚀 INMO AIR3 实时视频流 - 快速配置指南

## 📋 当前配置状态

✅ **后端服务器**: 已启动在 `http://192.168.2.19:5000`  
✅ **Android应用**: 已配置连接到正确的服务器地址  
✅ **WebSocket**: 已配置 `ws://192.168.2.19:5000/socket.io`  
✅ **网络安全**: 已配置允许HTTP明文通信  

## 🔒 网络安全配置

Android 9+ 默认禁止HTTP明文通信，本应用已配置网络安全策略：

- ✅ 允许本地网络HTTP通信
- ✅ 支持常见局域网IP范围
- ✅ 保持生产环境安全性

### 如果遇到"CLEARTEXT communication not permitted"错误：

1. **检查网络安全配置**: `app/src/main/res/xml/network_security_config.xml`
2. **添加你的服务器IP**: 在配置文件中添加新的domain条目
3. **重新构建应用**: 运行 `./gradlew assembleDebug`

## 🔧 如何修改服务器地址

### 方法1: 修改配置文件 (推荐)

编辑 `app/src/main/java/com/example/inmo/Config.kt`:

```kotlin
object Config {
    // 修改这里的IP地址
    const val SERVER_IP = "192.168.2.19"  // 改为你的服务器IP
    const val SERVER_PORT = 5000          // 改为你的服务器端口
    
    // 其他配置会自动更新
}
```

### 方法2: 查找当前服务器IP

如果不知道服务器IP，可以：

1. **Windows**: 运行 `ipconfig` 查看本机IP
2. **Linux/Mac**: 运行 `ifconfig` 或 `ip addr`
3. **后端启动时**: 控制台会显示服务器地址

## 📱 Android应用使用步骤

1. **安装APK**: 将生成的APK安装到INMO AIR3设备
2. **授予权限**: 
   - 摄像头权限 (必需)
   - 录音权限 (流传输需要)
   - 存储权限 (Android 9及以下)
3. **连接网络**: 确保设备与服务器在同一网络
4. **开始流传输**: 点击"开始流传输"按钮

## 🌐 网络要求

- **同一局域网**: Android设备和服务器必须在同一网络
- **防火墙**: 确保端口5000未被防火墙阻止
- **网络稳定**: 建议使用WiFi连接

## 🧪 测试连接

### 测试服务器状态
```bash
curl http://192.168.2.19:5000/
```

### 测试完整API
```bash
cd backend
python test_streaming.py
```

## 📊 性能调优

在 `Config.kt` 中可以调整：

```kotlin
// 帧率调整 (ms)
const val FRAME_CAPTURE_INTERVAL = 100L  // 100ms = 10FPS
                                         // 50ms = 20FPS
                                         // 33ms = 30FPS

// 数据块大小
const val CHUNK_SIZE = 8192  // 8KB (推荐)
                            // 4096 = 4KB (低带宽)
                            // 16384 = 16KB (高带宽)
```

## 🐛 常见问题解决

### 问题1: "CLEARTEXT communication not permitted"
**原因**: Android 9+ 默认禁止HTTP明文通信  
**解决**: 
1. 检查 `app/src/main/res/xml/network_security_config.xml`
2. 确保你的服务器IP在允许列表中
3. 重新构建并安装APK

### 问题2: "Unable to resolve host"
**解决**: 检查服务器IP地址是否正确，设备是否在同一网络

### 问题3: "Connection refused"
**解决**: 确保后端服务器正在运行，检查防火墙设置

### 问题4: "权限被拒绝"
**解决**: 在Android设置中手动授予所有权限

### 问题5: "流传输卡顿"
**解决**: 降低帧率或减小数据块大小

## 📋 检查清单

在开始使用前，请确认：

- [ ] 后端服务器正在运行
- [ ] Android设备与服务器在同一网络
- [ ] 服务器IP地址配置正确
- [ ] 所有权限已授予
- [ ] 防火墙允许端口5000访问

## 🎯 下一步

1. **启动后端**: `python backend/start_streaming_server.py`
2. **安装应用**: 安装生成的APK到INMO AIR3设备
3. **开始流传输**: 享受实时视频流体验！

---

🎉 **配置完成，开始体验实时视频流传输！**