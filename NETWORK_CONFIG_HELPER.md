# 🌐 网络配置助手

## 📱 Android网络安全配置说明

### 为什么需要网络安全配置？

从Android 9 (API 28) 开始，Google默认禁止应用使用HTTP明文通信，只允许HTTPS。但在开发环境中，我们通常使用HTTP协议连接本地服务器。

### 当前配置文件位置

`app/src/main/res/xml/network_security_config.xml`

### 如何添加新的服务器IP

如果你的服务器IP不是 `192.168.2.19`，需要在配置文件中添加：

```xml
<domain-config cleartextTrafficPermitted="true">
    <!-- 现有的域名 -->
    <domain includeSubdomains="true">localhost</domain>
    <domain includeSubdomains="true">127.0.0.1</domain>
    <domain includeSubdomains="true">192.168.2.19</domain>
    
    <!-- 添加你的服务器IP -->
    <domain includeSubdomains="true">YOUR_SERVER_IP</domain>
</domain-config>
```

### 常见IP地址范围

根据你的网络环境，可能需要添加以下IP：

#### 家庭网络
```xml
<domain includeSubdomains="true">192.168.1.1</domain>   <!-- 路由器常用IP -->
<domain includeSubdomains="true">192.168.0.1</domain>   <!-- 路由器常用IP -->
<domain includeSubdomains="true">192.168.1.100</domain> <!-- 设备IP示例 -->
```

#### 办公网络
```xml
<domain includeSubdomains="true">10.0.0.1</domain>      <!-- 企业网络 -->
<domain includeSubdomains="true">172.16.0.1</domain>    <!-- 企业网络 -->
```

#### 开发环境
```xml
<domain includeSubdomains="true">10.0.2.2</domain>      <!-- Android模拟器 -->
<domain includeSubdomains="true">localhost</domain>      <!-- 本机 -->
<domain includeSubdomains="true">127.0.0.1</domain>     <!-- 本机 -->
```

### 如何找到服务器IP地址

#### Windows
```cmd
ipconfig
```
查找 "IPv4 地址" 或 "IP Address"

#### Linux/Mac
```bash
ifconfig
# 或
ip addr show
```

#### 从后端启动日志
当你运行 `python start_streaming_server.py` 时，控制台会显示：
```
🌐 网络访问: http://YOUR_IP:5000
```

### 完整配置示例

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <!-- 本机地址 -->
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">127.0.0.1</domain>
        <domain includeSubdomains="true">10.0.2.2</domain>
        
        <!-- 你的服务器IP（替换为实际IP） -->
        <domain includeSubdomains="true">192.168.2.19</domain>
        
        <!-- 如果有多个可能的服务器IP，都可以添加 -->
        <domain includeSubdomains="true">192.168.1.100</domain>
        <domain includeSubdomains="true">10.0.0.50</domain>
    </domain-config>
    
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system"/>
        </trust-anchors>
    </base-config>
</network-security-config>
```

### 应用配置后的步骤

1. **修改配置文件** - 添加你的服务器IP
2. **更新Config.kt** - 修改 `SERVER_IP` 常量
3. **重新构建** - 运行 `./gradlew assembleDebug`
4. **安装新APK** - 安装到设备
5. **测试连接** - 启动应用测试

### 生产环境建议

在生产环境中，建议：

1. **使用HTTPS** - 在 `Config.kt` 中设置 `USE_HTTPS = true`
2. **配置SSL证书** - 为服务器配置有效的SSL证书
3. **移除HTTP支持** - 在网络安全配置中禁用明文通信

### 调试技巧

如果仍然遇到网络问题：

1. **检查日志**
   ```bash
   adb logcat | grep -i "network\|cleartext\|security"
   ```

2. **临时允许所有HTTP** (仅调试用)
   ```xml
   <base-config cleartextTrafficPermitted="true">
   ```

3. **验证服务器可达性**
   ```bash
   ping YOUR_SERVER_IP
   curl http://YOUR_SERVER_IP:5000/
   ```

---

🔧 **配置完成后，你的应用就能成功连接到服务器了！**