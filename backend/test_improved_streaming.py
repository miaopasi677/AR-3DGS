#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import time
import threading
import socketio
import json
import base64

# 服务器配置
SERVER_URL = "http://localhost:5000"

def test_improved_streaming():
    """测试改进后的流传输系统"""
    print("🧪 测试改进后的实时流传输系统...")
    print("-" * 60)
    
    # 1. 开始新流
    print("1️⃣ 开始新的视频流...")
    try:
        start_data = {"device_id": "test_device_improved"}
        response = requests.post(f"{SERVER_URL}/api/stream/start", json=start_data)
        
        if response.status_code == 200:
            result = response.json()
            if result['success']:
                stream_id = result['streamId']
                print(f"✅ 流开始成功，ID: {stream_id}")
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
    
    # 2. 测试WebSocket连接和处理后数据接收
    print("2️⃣ 测试WebSocket和处理后数据接收...")
    test_websocket_improved(stream_id)
    
    print()
    
    # 3. 发送测试数据块
    print("3️⃣ 发送测试视频数据...")
    send_test_chunks(stream_id)
    
    print()
    
    # 4. 停止流
    print("4️⃣ 停止视频流...")
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
    print("🎉 改进后的流传输系统测试完成！")
    return True

def test_websocket_improved(stream_id):
    """测试改进后的WebSocket功能"""
    try:
        sio = socketio.Client()
        processed_data_count = 0
        
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
            # 请求处理后的数据流
            sio.emit('request_processed_stream', {'stream_id': stream_id})
        
        @sio.on('processed_stream_started')
        def on_processed_stream_started(data):
            print(f"🎬 处理后数据流已启动: {data['stream_id']}")
        
        @sio.on('processed_chunk')
        def on_processed_chunk(data):
            nonlocal processed_data_count
            processed_data_count += 1
            
            try:
                # 解码base64数据
                base64_data = data['data']
                decoded_data = base64.b64decode(base64_data)
                
                print(f"📦 接收到处理后数据 #{processed_data_count}: {data['size']} bytes")
                
                # 检查是否包含时间戳
                if len(decoded_data) >= 8:
                    timestamp_bytes = decoded_data[:8]
                    timestamp = int.from_bytes(timestamp_bytes, byteorder='big')
                    print(f"   ⏰ 处理时间戳: {timestamp}")
                
            except Exception as e:
                print(f"   ❌ 解析处理后数据失败: {e}")
        
        @sio.on('processed_data_ready')
        def on_processed_data_ready(data):
            print(f"🆕 新的处理后数据就绪: {data['data_size']} bytes")
        
        @sio.on('new_chunk')
        def on_new_chunk(data):
            print(f"📥 新数据块通知: {data['chunk_size']} bytes")
        
        @sio.on('error')
        def on_error(data):
            print(f"❌ WebSocket错误: {data['message']}")
        
        # 连接到服务器
        sio.connect(SERVER_URL)
        
        # 等待接收数据
        print("⏳ 等待接收处理后的数据...")
        time.sleep(8)
        
        print(f"📊 总共接收到 {processed_data_count} 个处理后数据块")
        
        # 断开连接
        sio.disconnect()
        
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")

def send_test_chunks(stream_id):
    """发送测试数据块"""
    try:
        # 模拟YUV摄像头数据
        test_chunks = []
        
        # 创建不同的测试数据块
        for i in range(10):
            # 模拟YUV420数据（简化版）
            chunk_data = bytearray(1024)  # 1KB数据块
            
            # 填充模拟的YUV数据
            for j in range(len(chunk_data)):
                chunk_data[j] = (i * 25 + j) % 256
            
            test_chunks.append(bytes(chunk_data))
        
        print(f"📤 发送 {len(test_chunks)} 个测试数据块...")
        
        for i, chunk in enumerate(test_chunks):
            response = requests.post(
                f"{SERVER_URL}/api/stream/{stream_id}/chunk",
                data=chunk,
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
            
            time.sleep(0.2)  # 200ms间隔，模拟5FPS
            
    except Exception as e:
        print(f"❌ 发送测试数据失败: {e}")

if __name__ == '__main__':
    test_improved_streaming()