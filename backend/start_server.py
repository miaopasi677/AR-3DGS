#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess

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

def start_server():
    """启动服务器"""
    print("🚀 启动INMO AIR3视频处理服务器...")
    
    # 设置环境变量
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    
    try:
        # 启动Flask应用
        from app import app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    except ImportError:
        print("❌ 无法导入Flask应用，请检查依赖是否安装")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("🎥 INMO AIR3 视频处理服务器")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        sys.exit(1)
    
    # 安装依赖
    if not install_requirements():
        sys.exit(1)
    
    # 启动服务器
    start_server()