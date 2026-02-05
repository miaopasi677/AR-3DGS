#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import socketio
import time
import base64
import threading
from datetime import datetime

# 服务器配置
SERVER_URL = 'http://localhost:5000'
WEBSOCKET_URL = 'http://localhost:5000'

def test_websocket_processed_data():
    """测试WebSocket处理后数据接收"""
    print("🧪 测试WebSocket处理后数据接收...")
    print("-" * 60)
    
    # 1. 开始新的视频流
    print("1️⃣ 开始新的视频流...")
    response = requests.post(f'{SERVER_URL}/api/stream/start', json={
        'device_id': 'test_websocket_device'
    })
    
    if not response.ok or not response.json().get('success'):
        print(f"❌ 开始流失败: {response.text}")
        return False
    
    stream_id = response.json()['streamId']
    print(f"✅ 流开始成功，ID: {stream_id}")
    
    # 2. 连接WebSocket并请求处理后数据
    print("2️⃣ 连接WebSocket并请求处理后数据...")
    
    sio = socketio.Client()
    processed_data_received = []
    connection_success = threading.Event()
    stream_started = threading.Event()
    
    @sio.event
    def connect():
        print("✅ WebSocket连接成功")
        connection_success.set()
        
        # 加入流房间
        sio.emit('join_stream', {'stream_id': stream_id})
    
    @sio.event
    def disconnect():
        print("📡 WebSocket断开连接")
    
    @sio.on('joined_stream')
    def on_joined_stream(data):
        print(f"✅ 成功加入流房间: {data}")
        
        # 请求处理后的数据流
        sio.emit('request_processed_stream', {'stream_id': stream_id})
    
    @sio.on('processed_stream_started')
    def on_processed_stream_started(data):
        print(f"✅ 处理后数据流已启动: {data}")
        stream_started.set()
    
    @sio.on('processed_chunk')
    def on_processed_chunk(data):
        print(f"📦 接收到处理后数据块: 大小={data['size']} bytes, 时间戳={data['timestamp']}")
        processed_data_received.append(data)
    
    @sio.on('error')
    def on_error(data):
        print(f"❌ WebSocket错误: {data}")
    
    try:
        # 连接WebSocket
        sio.connect(WEBSOCKET_URL)
        
        # 等待连接成功
        if not connection_success.wait(timeout=5):
            print("❌ WebSocket连接超时")
            return False
        
        # 等待流启动
        if not stream_started.wait(timeout=5):
            print("❌ 处理后数据流启动超时")
            return False
        
        # 3. 发送测试数据
        print("3️⃣ 发送测试视频数据...")
        test_data = b'test_video_data_' * 100  # 1.5KB测试数据
        
        for i in range(5):
            chunk_data = test_data + f'_chunk_{i}'.encode()
            response = requests.post(
                f'{SERVER_URL}/api/stream/{stream_id}/chunk',
                data=chunk_data,
                headers={'Content-Type': 'application/octet-stream'}
            )
            
            if response.ok:
                print(f"✅ 数据块 {i+1} 发送成功")
            else:
                print(f"❌ 数据块 {i+1} 发送失败")
            
            time.sleep(0.5)  # 等待处理
        
        # 4. 等待接收处理后的数据
        print("4️⃣ 等待接收处理后的数据...")
        time.sleep(3)  # 等待3秒接收数据
        
        # 5. 验证结果
        print("5️⃣ 验证结果...")
        if len(processed_data_received) > 0:
            print(f"✅ 成功接收到 {len(processed_data_received)} 个处理后数据块")
            
            # 验证第一个数据块
            first_chunk = processed_data_received[0]
            decoded_data = base64.b64decode(first_chunk['data'])
            
            print(f"📊 第一个数据块详情:")
            print(f"   - 原始大小: {first_chunk['size']} bytes")
            print(f"   - 解码后大小: {len(decoded_data)} bytes")
            print(f"   - 时间戳: {first_chunk['timestamp']}")
            
            # 检查是否包含时间戳（前8字节）
            if len(decoded_data) >= 8:
                timestamp_bytes = decoded_data[:8]
                timestamp = int.from_bytes(timestamp_bytes, byteorder='big')
                print(f"   - 处理时间戳: {timestamp}")
                print("✅ 数据包含处理时间戳")
            
            print("✅ WebSocket处理后数据接收测试成功！")
            success = True
        else:
            print("❌ 未接收到任何处理后数据")
            success = False
        
        # 6. 停止流
        print("6️⃣ 停止视频流...")
        response = requests.post(f'{SERVER_URL}/api/stream/{stream_id}/stop')
        if response.ok:
            print("✅ 流停止成功")
        
        sio.disconnect()
        return success
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        return False

if __name__ == '__main__':
    print("🚀 开始WebSocket处理后数据测试...")
    print("=" * 60)
    
    success = test_websocket_processed_data()
    
    print("=" * 60)
    if success:
        print("🎉 所有测试通过！WebSocket处理后数据功能正常工作！")
    else:
        print("❌ 测试失败，请检查服务器配置")
    
    print("测试完成。")