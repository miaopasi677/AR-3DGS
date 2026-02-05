#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, send_file, url_for
from flask_cors import CORS
import os
import uuid
import time
import threading
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# 视频处理状态存储
video_status = {}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def simulate_video_processing(video_id, input_path, output_path):
    """模拟视频处理过程"""
    try:
        logger.info(f"开始处理视频 {video_id}")
        video_status[video_id]['status'] = 'processing'
        
        # 模拟处理时间（5-10秒）
        processing_time = 8
        for i in range(processing_time):
            time.sleep(1)
            progress = (i + 1) / processing_time * 100
            logger.info(f"视频 {video_id} 处理进度: {progress:.1f}%")
        
        # 简单的"处理"：复制原文件到processed目录
        # 在实际应用中，这里可以调用FFmpeg或其他视频处理工具
        import shutil
        shutil.copy2(input_path, output_path)
        
        # 更新状态为完成
        video_status[video_id]['status'] = 'completed'
        video_status[video_id]['processed_video_url'] = f"/api/video/{video_id}"
        video_status[video_id]['completed_at'] = datetime.now().isoformat()
        
        logger.info(f"视频 {video_id} 处理完成")
        
    except Exception as e:
        logger.error(f"视频 {video_id} 处理失败: {str(e)}")
        video_status[video_id]['status'] = 'failed'
        video_status[video_id]['error'] = str(e)

@app.route('/')
def index():
    """首页"""
    return jsonify({
        'message': 'INMO AIR3 视频处理服务器',
        'version': '1.0.0',
        'endpoints': {
            'upload': '/api/upload/video',
            'status': '/api/video/{videoId}/status',
            'download': '/api/video/{videoId}'
        }
    })

@app.route('/api/upload/video', methods=['POST'])
def upload_video():
    """上传视频接口"""
    try:
        # 检查是否有文件
        if 'video' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有找到视频文件'
            }), 400
        
        file = request.files['video']
        device_id = request.form.get('device_id', 'unknown')
        
        # 检查文件名
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        # 检查文件类型
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': '不支持的文件格式'
            }), 400
        
        # 生成唯一的视频ID
        video_id = str(uuid.uuid4())
        
        # 保存文件
        filename = f"{video_id}.mp4"
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(PROCESSED_FOLDER, filename)
        
        file.save(input_path)
        
        # 记录视频信息
        video_status[video_id] = {
            'video_id': video_id,
            'device_id': device_id,
            'original_filename': file.filename,
            'status': 'uploaded',
            'uploaded_at': datetime.now().isoformat(),
            'input_path': input_path,
            'output_path': output_path
        }
        
        # 启动后台处理线程
        processing_thread = threading.Thread(
            target=simulate_video_processing,
            args=(video_id, input_path, output_path)
        )
        processing_thread.daemon = True
        processing_thread.start()
        
        logger.info(f"视频上传成功: {video_id}, 设备: {device_id}, 文件: {file.filename}")
        
        return jsonify({
            'success': True,
            'videoId': video_id,
            'message': '视频上传成功，开始处理'
        })
        
    except Exception as e:
        logger.error(f"上传视频失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }), 500

@app.route('/api/video/<video_id>/status', methods=['GET'])
def get_video_status(video_id):
    """获取视频处理状态"""
    try:
        if video_id not in video_status:
            return jsonify({
                'success': False,
                'message': '视频不存在'
            }), 404
        
        status_info = video_status[video_id]
        
        response = {
            'success': True,
            'status': status_info['status'],
            'message': f"视频状态: {status_info['status']}"
        }
        
        # 如果处理完成，添加下载链接
        if status_info['status'] == 'completed':
            # 使用完整的URL
            response['processedVideoUrl'] = request.url_root.rstrip('/') + f"/api/video/{video_id}"
        
        # 如果处理失败，添加错误信息
        if status_info['status'] == 'failed':
            response['error'] = status_info.get('error', '未知错误')
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"获取视频状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取状态失败: {str(e)}'
        }), 500

@app.route('/api/video/<video_id>', methods=['GET'])
def download_video(video_id):
    """下载处理后的视频"""
    try:
        if video_id not in video_status:
            return jsonify({
                'success': False,
                'message': '视频不存在'
            }), 404
        
        status_info = video_status[video_id]
        
        if status_info['status'] != 'completed':
            return jsonify({
                'success': False,
                'message': f"视频尚未处理完成，当前状态: {status_info['status']}"
            }), 400
        
        output_path = status_info['output_path']
        
        if not os.path.exists(output_path):
            return jsonify({
                'success': False,
                'message': '处理后的视频文件不存在'
            }), 404
        
        logger.info(f"下载视频: {video_id}")
        
        return send_file(
            output_path,
            as_attachment=False,
            download_name=f"processed_{video_id}.mp4",
            mimetype='video/mp4'
        )
        
    except Exception as e:
        logger.error(f"下载视频失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'下载失败: {str(e)}'
        }), 500

@app.route('/api/videos', methods=['GET'])
def list_videos():
    """列出所有视频（调试用）"""
    try:
        videos = []
        for video_id, info in video_status.items():
            videos.append({
                'video_id': video_id,
                'device_id': info.get('device_id'),
                'status': info['status'],
                'uploaded_at': info.get('uploaded_at'),
                'completed_at': info.get('completed_at')
            })
        
        return jsonify({
            'success': True,
            'videos': videos,
            'total': len(videos)
        })
        
    except Exception as e:
        logger.error(f"列出视频失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取视频列表失败: {str(e)}'
        }), 500

@app.route('/api/cleanup', methods=['POST'])
def cleanup_old_videos():
    """清理旧视频文件（调试用）"""
    try:
        cleaned_count = 0
        
        # 清理超过1小时的视频
        current_time = datetime.now()
        to_remove = []
        
        for video_id, info in video_status.items():
            uploaded_time = datetime.fromisoformat(info['uploaded_at'])
            if (current_time - uploaded_time).total_seconds() > 3600:  # 1小时
                to_remove.append(video_id)
        
        for video_id in to_remove:
            info = video_status[video_id]
            
            # 删除文件
            for path in [info.get('input_path'), info.get('output_path')]:
                if path and os.path.exists(path):
                    os.remove(path)
            
            # 删除状态记录
            del video_status[video_id]
            cleaned_count += 1
        
        logger.info(f"清理了 {cleaned_count} 个旧视频")
        
        return jsonify({
            'success': True,
            'message': f'清理了 {cleaned_count} 个旧视频'
        })
        
    except Exception as e:
        logger.error(f"清理视频失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'清理失败: {str(e)}'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500

if __name__ == '__main__':
    print("🚀 INMO AIR3 视频处理服务器启动中...")
    print("📡 服务器地址: http://localhost:5000")
    print("📋 API文档: http://localhost:5000")
    print("🎥 上传接口: http://localhost:5000/api/upload/video")
    print("📊 视频列表: http://localhost:5000/api/videos")
    
    # 开发模式运行
    app.run(
        host='0.0.0.0',  # 允许外部访问
        port=5000,
        debug=True,
        threaded=True
    )