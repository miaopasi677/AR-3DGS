#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import threading
import socketio
import json

# 服务器配置
SERVER_URL = "http://localhost:5000"

def test_streaming_api():
    """测试流传输API"""
    print("🧪 测试实时流传输API...")
    print("-" * 50)
    
    # 1. 测试服务器状态
    print("1️⃣ 测试服务器状态...")
    try:
        response = requests.get(f"{SERVER_URL}/")
        if response.status_code == 200:
            print("✅ 服务器运行正常")
            server_info = response.json()
            print(f"📋 服务器信息: {server_info['message']}")
            print(f"🔧 版本: {server_info['version']}")
        else:
            print(f"❌ 服务器响应异常: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器已启动")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    print()
    
    # 2. 开始新流
    print("2️⃣ 开始新的视频流...")
    try:
        start_data = {
            "device_id": "test_device_streaming"
        }
        response = requests.post(f"{SERVER_URL}/api/stream/start", json=start_data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                stream_id = result['streamId']
                print(f"✅ 流开始成功，ID: {stream_id}")
                print(f"🔌 WebSocket URL: {result.get('websocket_url', 'N/A')}")
            else:
                print(f"❌ 开始流失败: {result['message']}")
                return False
        else:
            print(f"❌ 开始流请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 开始流测试失败: {e}")
        return False
    
    print()
    
    # 3. 发送测试数据块
    print("3️⃣ 发送测试数据块...")
    try:
        test_data = b"fake video chunk data for testing" * 100  # 模拟视频数据
        
        for i in range(5):
            response = requests.post(
                f"{SERVER_URL}/api/stream/{stream_id}/chunk",
                data=test_data,
                headers={'Content-Type': 'application/octet-stream'}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['success']:
                    print(f"✅ 数据块 {i+1} 发送成功")
                else:
                    print(f"❌ 数据块 {i+1} 发送失败: {result['message']}")
            else:
                print(f"❌ 数据块 {i+1} 请求失败: {response.status_code}")
            
            time.sleep(0.5)  # 500ms间隔
            
    except Exception as e:
        print(f"❌ 发送数据块测试失败: {e}")
    
    print()
    
    # 4. 测试WebSocket连接
    print("4️⃣ 测试WebSocket连接...")
    test_websocket(stream_id)
    
    print()
    
    # 5. 获取流列表
    print("5️⃣ 获取流列表...")
    try:
        response = requests.get(f"{SERVER_URL}/api/streams")
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                streams = result['streams']
                print(f"✅ 获取到 {result['total']} 个流:")
                for stream in streams:
                    print(f"   📺 流ID: {stream['stream_id']}")
                    print(f"      设备: {stream['device_id']}")
                    print(f"      状态: {'🟢 活跃' if stream['is_active'] else '🔴 停止'}")
                    print(f"      客户端: {stream['clients_count']}")
                    print(f"      缓冲区: {stream['buffer_size']}")
            else:
                print(f"❌ 获取流列表失败: {result['message']}")
        else:
            print(f"❌ 获取流列表请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 获取流列表测试失败: {e}")
    
    print()
    
    # 6. 停止流
    print("6️⃣ 停止视频流...")
    try:
        response = requests.post(f"{SERVER_URL}/api/stream/{stream_id}/stop")
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                print("✅ 流停止成功")
            else:
                print(f"❌ 停止流失败: {result['message']}")
        else:
            print(f"❌ 停止流请求失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 停止流测试失败: {e}")
    
    print()
    print("🎉 流传输API测试完成！")
    return True

def test_websocket(stream_id):
    """测试WebSocket连接"""
    try:
        sio = socketio.Client()
        
        @sio.event
        def connect():
            print("✅ WebSocket连接成功")
            # 加入流房间
            sio.emit('join_stream', {'stream_id': stream_id})
        
        @sio.event
        def disconnect():
            print("📡 WebSocket断开连接")
        
        @sio.on('joined_stream')
        def on_joined_stream(data):
            print(f"✅ 成功加入流: {data['stream_id']}")
            
            # 请求处理后的数据
            for i in range(3):
                sio.emit('get_processed_chunk', {'stream_id': stream_id})
                time.sleep(1)
        
        @sio.on('processed_chunk')
        def on_processed_chunk(data):
            print(f"📦 接收到处理后数据: {data['size']} bytes")
        
        @sio.on('no_data')
        def on_no_data(data):
            print("📭 暂无处理后数据")
        
        @sio.on('new_chunk')
        def on_new_chunk(data):
            print(f"🆕 新数据块通知: {data['chunk_size']} bytes")
        
        @sio.on('error')
        def on_error(data):
            print(f"❌ WebSocket错误: {data['message']}")
        
        # 连接到服务器
        sio.connect(SERVER_URL)
        
        # 等待一段时间接收消息
        time.sleep(5)
        
        # 离开流房间
        sio.emit('leave_stream', {'stream_id': stream_id})
        time.sleep(1)
        
        # 断开连接
        sio.disconnect()
        
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")

if __name__ == '__main__':
    test_streaming_api()