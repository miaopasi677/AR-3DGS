#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import os

# 服务器配置
SERVER_URL = "http://localhost:5000"

def test_server_status():
    """测试服务器状态"""
    try:
        response = requests.get(f"{SERVER_URL}/")
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            print(f"📋 服务器信息: {response.json()}")
            return True
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器已启动")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_upload_video():
    """测试视频上传"""
    # 创建一个测试视频文件（空文件）
    test_video_path = "test_video.mp4"
    
    try:
        # 创建测试文件
        with open(test_video_path, 'wb') as f:
            f.write(b'fake video content for testing')
        
        # 上传文件
        with open(test_video_path, 'rb') as f:
            files = {'video': ('test_video.mp4', f, 'video/mp4')}
            data = {'device_id': 'test_device_123'}
            
            response = requests.post(f"{SERVER_URL}/api/upload/video", files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                video_id = result['videoId']
                print(f"✅ 视频上传成功，ID: {video_id}")
                return video_id
            else:
                print(f"❌ 上传失败: {result['message']}")
                return None
        else:
            print(f"❌ 上传请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 上传测试失败: {e}")
        return None
    finally:
        # 清理测试文件
        if os.path.exists(test_video_path):
            os.remove(test_video_path)

def test_video_status(video_id):
    """测试视频状态查询"""
    try:
        response = requests.get(f"{SERVER_URL}/api/video/{video_id}/status")
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                status = result['status']
                print(f"📊 视频状态: {status}")
                
                if status == 'completed' and 'processedVideoUrl' in result:
                    print(f"🎥 处理完成，下载链接: {result['processedVideoUrl']}")
                
                return status
            else:
                print(f"❌ 状态查询失败: {result['message']}")
                return None
        else:
            print(f"❌ 状态查询请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ 状态查询测试失败: {e}")
        return None

def test_video_download(video_id):
    """测试视频下载"""
    try:
        response = requests.get(f"{SERVER_URL}/api/video/{video_id}")
        
        if response.status_code == 200:
            print(f"✅ 视频下载成功，大小: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ 视频下载失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 下载测试失败: {e}")
        return False

def main():
    """主测试流程"""
    print("🧪 开始API测试...")
    print("-" * 40)
    
    # 1. 测试服务器状态
    print("1️⃣ 测试服务器状态...")
    if not test_server_status():
        return
    
    print()
    
    # 2. 测试视频上传
    print("2️⃣ 测试视频上传...")
    video_id = test_upload_video()
    if not video_id:
        return
    
    print()
    
    # 3. 测试状态查询（等待处理完成）
    print("3️⃣ 测试状态查询...")
    max_wait_time = 30  # 最多等待30秒
    wait_time = 0
    
    while wait_time < max_wait_time:
        status = test_video_status(video_id)
        
        if status == 'completed':
            break
        elif status == 'failed':
            print("❌ 视频处理失败")
            return
        elif status in ['uploaded', 'processing']:
            print(f"⏳ 等待处理完成... ({wait_time}s)")
            time.sleep(2)
            wait_time += 2
        else:
            print(f"❌ 未知状态: {status}")
            return
    
    if wait_time >= max_wait_time:
        print("⏰ 等待超时")
        return
    
    print()
    
    # 4. 测试视频下载
    print("4️⃣ 测试视频下载...")
    test_video_download(video_id)
    
    print()
    print("🎉 所有测试完成！")

if __name__ == '__main__':
    main()