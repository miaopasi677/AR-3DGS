#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import socket

def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result == 0

def install_requirements():
    """安装依赖"""
    print("📦 安装Python依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False
    return True

def get_local_ip():
    """获取本机IP地址"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def start_streaming_server():
    """启动流传输服务器"""
    print("🚀 启动INMO AIR3实时视频流处理服务器...")
    
    # 检查端口
    port = 5000
    if check_port(port):
        print(f"⚠️  端口 {port} 已被占用，请关闭占用该端口的程序")
        return False
    
    # 获取本机IP
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("🎥 INMO AIR3 实时视频流处理服务器")
    print("=" * 60)
    print(f"📡 本地访问: http://localhost:{port}")
    print(f"🌐 网络访问: http://{local_ip}:{port}")
    print(f"🔌 WebSocket: ws://{local_ip}:{port}/socket.io")
    print("=" * 60)
    print("📋 API接口:")
    print(f"   开始流: POST http://{local_ip}:{port}/api/stream/start")
    print(f"   上传块: POST http://{local_ip}:{port}/api/stream/{{streamId}}/chunk")
    print(f"   获取流: GET  http://{local_ip}:{port}/api/stream/{{streamId}}")
    print(f"   停止流: POST http://{local_ip}:{port}/api/stream/{{streamId}}/stop")
    print(f"   流列表: GET  http://{local_ip}:{port}/api/streams")
    print("=" * 60)
    print("📱 Android应用配置:")
    print(f"   在 StreamingManager 中将服务器地址改为: http://{local_ip}:{port}")
    print("=" * 60)
    print("🔧 控制命令:")
    print("   Ctrl+C: 停止服务器")
    print("=" * 60)
    
    try:
        # 启动Flask-SocketIO应用
        from streaming_app import app, socketio
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=False,  # 生产模式
            allow_unsafe_werkzeug=True
        )
    except ImportError:
        print("❌ 无法导入流传输应用，请检查 streaming_app.py 文件")
        return False
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        return True
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        return False

if __name__ == '__main__':
    print("🎬 INMO AIR3 实时视频流处理服务器启动器")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        sys.exit(1)
    
    # 安装依赖
    if not install_requirements():
        sys.exit(1)
    
    print()
    
    # 启动服务器
    if not start_streaming_server():
        sys.exit(1)