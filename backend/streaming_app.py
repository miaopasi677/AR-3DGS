#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, Response, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import uuid
import time
import threading
import queue
import base64
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'inmo_air3_streaming_secret'
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 流媒体配置
CHUNK_SIZE = 8192  # 8KB chunks
MAX_BUFFER_SIZE = 100  # 最大缓冲区大小

# 存储活跃的流
active_streams = {}
stream_buffers = {}

class VideoStream:
    def __init__(self, stream_id, device_id):
        self.stream_id = stream_id
        self.device_id = device_id
        self.created_at = datetime.now()
        self.is_active = True
        self.chunk_queue = queue.Queue(maxsize=MAX_BUFFER_SIZE)
        self.processed_queue = queue.Queue(maxsize=MAX_BUFFER_SIZE)
        self.clients = set()
        
    def add_chunk(self, chunk_data):
        """添加视频数据块"""
        try:
            if not self.chunk_queue.full():
                self.chunk_queue.put(chunk_data, block=False)
                return True
            else:
                logger.warning(f"Stream {self.stream_id} buffer full, dropping chunk")
                return False
        except queue.Full:
            return False
    
    def get_processed_chunk(self, timeout=1.0):
        """获取处理后的数据块"""
        try:
            return self.processed_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def add_client(self, client_id):
        """添加客户端"""
        self.clients.add(client_id)
        logger.info(f"Client {client_id} joined stream {self.stream_id}")
    
    def remove_client(self, client_id):
        """移除客户端"""
        self.clients.discard(client_id)
        logger.info(f"Client {client_id} left stream {self.stream_id}")
    
    def stop(self):
        """停止流"""
        self.is_active = False

def simulate_video_processing(stream):
    """模拟实时视频处理"""
    logger.info(f"开始处理流 {stream.stream_id}")
    
    while stream.is_active:
        try:
            # 从输入队列获取数据
            chunk_data = stream.chunk_queue.get(timeout=1.0)
            
            # 模拟处理延迟
            time.sleep(0.05)  # 50ms处理延迟
            
            # 简单的视频处理：添加时间戳和滤镜效果
            processed_data = process_video_chunk(chunk_data, stream.stream_id)
            
            # 将处理后的数据放入输出队列
            if not stream.processed_queue.full():
                stream.processed_queue.put(processed_data, block=False)
                
                # 使用app上下文发送WebSocket消息
                with app.app_context():
                    socketio.emit('processed_data_ready', {
                        'stream_id': stream.stream_id,
                        'data_size': len(processed_data),
                        'timestamp': datetime.now().isoformat()
                    }, room=f'stream_{stream.stream_id}')
            
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"处理流 {stream.stream_id} 时出错: {e}")
            break
    
    logger.info(f"流 {stream.stream_id} 处理结束")

def process_video_chunk(chunk_data, stream_id):
    """处理视频数据块"""
    try:
        # 这里可以添加真正的视频处理逻辑
        # 例如：滤镜、特效、格式转换等
        
        # 模拟添加时间戳（在数据开头添加时间信息）
        timestamp = int(time.time() * 1000).to_bytes(8, byteorder='big')
        
        # 创建新的bytearray，先添加时间戳，再添加原始数据
        processed_data = bytearray(timestamp)
        processed_data.extend(chunk_data)
        
        # 轻量级的视频处理（减少计算量）
        video_data_start = 8  # 跳过时间戳
        video_data_size = len(chunk_data)
        
        # 只对部分数据进行处理以提高性能
        # 每隔10个像素处理一次，减少计算量
        for i in range(video_data_start, min(video_data_start + video_data_size // 10, len(processed_data)), 10):
            if i < len(processed_data):
                original_value = processed_data[i]
                # 轻微的亮度调整
                adjusted_value = min(255, max(0, original_value + 10))
                processed_data[i] = adjusted_value
        
        # 只在第一次处理时记录日志，减少日志输出
        if not hasattr(process_video_chunk, 'log_count'):
            process_video_chunk.log_count = 0
        
        process_video_chunk.log_count += 1
        if process_video_chunk.log_count % 10 == 1:  # 每10帧记录一次
            logger.info(f"处理视频数据: 原始大小={video_data_size}, 处理后大小={len(processed_data)}")
        
        return bytes(processed_data)
        
    except Exception as e:
        logger.error(f"处理视频数据失败: {e}")
        return chunk_data  # 返回原始数据

@app.route('/')
def index():
    """首页"""
    return jsonify({
        'message': 'INMO AIR3 实时视频流处理服务器',
        'version': '2.0.0',
        'features': ['real-time streaming', 'websocket support', 'live processing'],
        'endpoints': {
            'start_stream': '/api/stream/start',
            'upload_chunk': '/api/stream/{streamId}/chunk',
            'get_stream': '/api/stream/{streamId}',
            'websocket': '/socket.io'
        }
    })

@app.route('/api/stream/start', methods=['POST'])
def start_stream():
    """开始新的视频流"""
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id', 'unknown')
        
        # 生成流ID
        stream_id = str(uuid.uuid4())
        
        # 创建新流
        stream = VideoStream(stream_id, device_id)
        active_streams[stream_id] = stream
        
        # 启动处理线程
        processing_thread = threading.Thread(
            target=simulate_video_processing,
            args=(stream,)
        )
        processing_thread.daemon = True
        processing_thread.start()
        
        logger.info(f"新流开始: {stream_id}, 设备: {device_id}")
        
        return jsonify({
            'success': True,
            'streamId': stream_id,
            'message': '流开始成功',
            'websocket_url': f'/stream/{stream_id}'
        })
        
    except Exception as e:
        logger.error(f"开始流失败: {e}")
        return jsonify({
            'success': False,
            'message': f'开始流失败: {str(e)}'
        }), 500

@app.route('/api/stream/<stream_id>/chunk', methods=['POST'])
def upload_chunk(stream_id):
    """上传视频数据块"""
    try:
        if stream_id not in active_streams:
            return jsonify({
                'success': False,
                'message': '流不存在'
            }), 404
        
        stream = active_streams[stream_id]
        
        if not stream.is_active:
            return jsonify({
                'success': False,
                'message': '流已停止'
            }), 400
        
        # 获取数据块
        chunk_data = request.data
        
        if len(chunk_data) == 0:
            return jsonify({
                'success': False,
                'message': '数据块为空'
            }), 400
        
        # 添加到流缓冲区
        success = stream.add_chunk(chunk_data)
        
        if success:
            # 通知WebSocket客户端有新数据
            with app.app_context():
                socketio.emit('new_chunk', {
                    'stream_id': stream_id,
                    'chunk_size': len(chunk_data),
                    'timestamp': datetime.now().isoformat()
                }, room=f'stream_{stream_id}')
            
            return jsonify({
                'success': True,
                'message': '数据块接收成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '缓冲区已满'
            }), 429
        
    except Exception as e:
        logger.error(f"上传数据块失败: {e}")
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }), 500

@app.route('/api/stream/<stream_id>')
def get_stream(stream_id):
    """获取处理后的视频流"""
    try:
        if stream_id not in active_streams:
            return jsonify({
                'success': False,
                'message': '流不存在'
            }), 404
        
        stream = active_streams[stream_id]
        
        def generate():
            """生成流数据"""
            while stream.is_active:
                chunk = stream.get_processed_chunk(timeout=2.0)
                if chunk is not None:
                    yield chunk
                else:
                    # 发送心跳数据
                    yield b''
        
        return Response(
            generate(),
            mimetype='application/octet-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*'
            }
        )
        
    except Exception as e:
        logger.error(f"获取流失败: {e}")
        return jsonify({
            'success': False,
            'message': f'获取流失败: {str(e)}'
        }), 500

@app.route('/api/stream/<stream_id>/stop', methods=['POST'])
def stop_stream(stream_id):
    """停止视频流"""
    try:
        if stream_id not in active_streams:
            return jsonify({
                'success': False,
                'message': '流不存在'
            }), 404
        
        stream = active_streams[stream_id]
        stream.stop()
        
        # 通知所有客户端流已停止
        with app.app_context():
            socketio.emit('stream_stopped', {
                'stream_id': stream_id,
                'timestamp': datetime.now().isoformat()
            }, room=f'stream_{stream_id}')
        
        # 清理资源
        del active_streams[stream_id]
        
        logger.info(f"流停止: {stream_id}")
        
        return jsonify({
            'success': True,
            'message': '流停止成功'
        })
        
    except Exception as e:
        logger.error(f"停止流失败: {e}")
        return jsonify({
            'success': False,
            'message': f'停止流失败: {str(e)}'
        }), 500

@app.route('/api/streams', methods=['GET'])
def list_streams():
    """列出所有活跃的流"""
    try:
        streams = []
        for stream_id, stream in active_streams.items():
            streams.append({
                'stream_id': stream_id,
                'device_id': stream.device_id,
                'is_active': stream.is_active,
                'created_at': stream.created_at.isoformat(),
                'clients_count': len(stream.clients),
                'buffer_size': stream.chunk_queue.qsize()
            })
        
        return jsonify({
            'success': True,
            'streams': streams,
            'total': len(streams)
        })
        
    except Exception as e:
        logger.error(f"列出流失败: {e}")
        return jsonify({
            'success': False,
            'message': f'列出流失败: {str(e)}'
        }), 500

# WebSocket事件处理
@socketio.on('connect')
def handle_connect():
    """客户端连接"""
    logger.info(f"WebSocket客户端连接: {request.sid}")
    emit('connected', {'message': '连接成功', 'client_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """客户端断开连接"""
    logger.info(f"WebSocket客户端断开: {request.sid}")
    
    # 从所有流中移除该客户端
    for stream in active_streams.values():
        stream.remove_client(request.sid)

@socketio.on('join_stream')
def handle_join_stream(data):
    """加入视频流"""
    try:
        stream_id = data.get('stream_id')
        
        if not stream_id or stream_id not in active_streams:
            emit('error', {'message': '流不存在'})
            return
        
        stream = active_streams[stream_id]
        room = f'stream_{stream_id}'
        
        join_room(room)
        stream.add_client(request.sid)
        
        emit('joined_stream', {
            'stream_id': stream_id,
            'message': '成功加入流'
        })
        
        logger.info(f"客户端 {request.sid} 加入流 {stream_id}")
        
    except Exception as e:
        logger.error(f"加入流失败: {e}")
        emit('error', {'message': f'加入流失败: {str(e)}'})

@socketio.on('leave_stream')
def handle_leave_stream(data):
    """离开视频流"""
    try:
        stream_id = data.get('stream_id')
        
        if stream_id and stream_id in active_streams:
            stream = active_streams[stream_id]
            room = f'stream_{stream_id}'
            
            leave_room(room)
            stream.remove_client(request.sid)
            
            emit('left_stream', {
                'stream_id': stream_id,
                'message': '成功离开流'
            })
            
            logger.info(f"客户端 {request.sid} 离开流 {stream_id}")
        
    except Exception as e:
        logger.error(f"离开流失败: {e}")
        emit('error', {'message': f'离开流失败: {str(e)}'})

@socketio.on('get_processed_chunk')
def handle_get_processed_chunk(data):
    """获取处理后的数据块"""
    try:
        stream_id = data.get('stream_id')
        
        if not stream_id or stream_id not in active_streams:
            emit('error', {'message': '流不存在'})
            return
        
        stream = active_streams[stream_id]
        chunk = stream.get_processed_chunk(timeout=0.1)
        
        if chunk is not None:
            # 将二进制数据编码为base64
            chunk_b64 = base64.b64encode(chunk).decode('utf-8')
            emit('processed_chunk', {
                'stream_id': stream_id,
                'data': chunk_b64,
                'size': len(chunk),
                'timestamp': datetime.now().isoformat()
            })
        else:
            emit('no_data', {'stream_id': stream_id})
        
    except Exception as e:
        logger.error(f"获取处理数据失败: {e}")
        emit('error', {'message': f'获取数据失败: {str(e)}'})

@socketio.on('request_processed_stream')
def handle_request_processed_stream(data):
    """请求处理后的数据流"""
    try:
        stream_id = data.get('stream_id')
        
        if not stream_id or stream_id not in active_streams:
            emit('error', {'message': '流不存在'})
            return
        
        stream = active_streams[stream_id]
        client_sid = request.sid  # 保存客户端ID
        
        # 启动一个线程持续发送处理后的数据
        def send_processed_stream():
            while stream.is_active and client_sid in stream.clients:
                chunk = stream.get_processed_chunk(timeout=1.0)
                if chunk is not None:
                    chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                    with app.app_context():
                        socketio.emit('processed_chunk', {
                            'stream_id': stream_id,
                            'data': chunk_b64,
                            'size': len(chunk),
                            'timestamp': datetime.now().isoformat()
                        }, room=client_sid)
                    time.sleep(0.2)  # 5 FPS，匹配帧捕获频率
        
        import threading
        thread = threading.Thread(target=send_processed_stream)
        thread.daemon = True
        thread.start()
        
        emit('processed_stream_started', {'stream_id': stream_id})
        
    except Exception as e:
        logger.error(f"启动处理数据流失败: {e}")
        emit('error', {'message': f'启动数据流失败: {str(e)}'})

if __name__ == '__main__':
    print("🚀 INMO AIR3 实时视频流处理服务器启动中...")
    print("📡 服务器地址: http://localhost:5000")
    print("🔌 WebSocket地址: ws://localhost:5000/socket.io")
    print("📋 API文档: http://localhost:5000")
    print("🎥 开始流: POST http://localhost:5000/api/stream/start")
    print("📊 流列表: http://localhost:5000/api/streams")
    
    # 启动服务器
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )