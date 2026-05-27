#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiMo 声音克隆 Web 平台
使用方法：python app.py
"""

import os
import io
import sys
import json
import base64
import uuid
import shutil
import re
import threading
import requests
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, request, render_template, jsonify, send_file, url_for
from werkzeug.utils import secure_filename

# 修复编码问题
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except:
    pass

# 创建Flask应用
app = Flask(__name__, static_folder='static', template_folder='templates')

# 全局配置（从 config.json 读取）
config = {}

# ==================== 热加载配置（文件存储，支持 Passenger 多进程）====================
hot_config_file = Path(__file__).parent / 'hot_config.json'
hot_config_lock = threading.Lock()


def load_hot_config():
    """从文件加载热配置（支持多进程共享）"""
    try:
        if hot_config_file.exists():
            with open(hot_config_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
    except Exception as e:
        print(f"[WARN] 读取热配置文件失败: {e}")
    return {'api_key': None, 'api_url': None}


def save_hot_config_to_file(hot_config):
    """保存热配置到文件（支持多进程共享）"""
    try:
        temp_file = hot_config_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(hot_config, f, ensure_ascii=False)
        temp_file.replace(hot_config_file)
        print(f"[OK] 热配置已保存到文件: {hot_config_file}")
    except Exception as e:
        print(f"[ERR] 保存热配置文件失败: {e}")


def get_effective_api_key():
    """获取有效的 API Key（热配置文件优先，其次 config.json）"""
    with hot_config_lock:
        hot_config = load_hot_config()
        if hot_config.get('api_key'):
            return hot_config['api_key']
    return config.get('api_key', '')


def get_effective_api_url():
    """获取有效的 API URL（热配置文件优先，其次 config.json）"""
    with hot_config_lock:
        hot_config = load_hot_config()
        if hot_config.get('api_url'):
            return hot_config['api_url']
    return config.get('api_url', '')


def get_effective_model_name():
    """获取有效的模型名称（始终读取 config.json）"""
    return config.get('model_name', '')


# ==================== 配置加载 ====================

def load_config():
    """加载配置文件"""
    global config
    
    defaults = {
        "api_url": "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
        "model_name": "mimo-v2.5-tts-voiceclone",
        "api_key": "",
        "port": 8080,
        "host": "0.0.0.0",
        "max_file_size_mb": 50,
        "allowed_extensions": ["wav", "mp3", "ogg", "flac"],
        "output_dir": "outputs",
        "auto_cleanup_hours": 24,
        "default_text": "你好，这是声音克隆测试",
        "debug_mode": False
    }
    config = defaults.copy()
    
    config_path = Path(__file__).parent / 'config.json'
    
    if not config_path.exists():
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(defaults, f, indent=4, ensure_ascii=False)
            print(f"[OK] 配置文件已创建: {config_path}")
        except Exception as e:
            print(f"[WARN] 无法创建配置文件: {e}，使用默认配置")
    else:
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    file_config = json.loads(content)
                    for key, value in file_config.items():
                        if value is not None and value != '':
                            config[key] = value
                    print(f"[OK] 配置文件加载成功: {config_path}")
                else:
                    print(f"[WARN] 配置文件为空，使用默认配置")
        except json.JSONDecodeError as e:
            print(f"[WARN] 配置文件格式错误: {e}，使用默认配置")
        except Exception as e:
            print(f"[WARN] 配置文件读取失败: {e}，使用默认配置")
    
    # 确保所有字段都有值
    for key, value in defaults.items():
        if key not in config or config[key] is None:
            config[key] = value
    
    # 创建必要目录
    try:
        Path(config.get('output_dir', 'outputs')).mkdir(exist_ok=True)
        Path('uploads').mkdir(exist_ok=True)
    except Exception as e:
        print(f"[WARN] 创建目录失败: {e}")
    
    print(f"[OK] 配置加载完成 - API URL: {config.get('api_url', 'N/A')}")
    print(f"[OK] 配置加载完成 - Model: {config.get('model_name', 'N/A')}")
    print(f"[OK] 配置加载完成 - API Key: {'已配置' if config.get('api_key') else '未配置'}")
    
    return True


def allowed_file(filename):
    """检查文件是否允许上传"""
    allowed = config.get('allowed_extensions', ['wav', 'mp3', 'ogg', 'flac'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed


def generate_unique_filename(extension):
    """生成唯一的文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"{timestamp}_{unique_id}.{extension}"


def cleanup_old_files():
    """清理过期的输出文件"""
    output_dir = Path(config.get('output_dir', 'outputs'))
    if not output_dir.exists():
        return
    
    hours = config.get('auto_cleanup_hours', 24)
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    for file_path in output_dir.glob("*"):
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_time < cutoff_time:
                try:
                    file_path.unlink()
                    print(f"[DEL] 已清理过期文件: {file_path.name}")
                except:
                    pass


def clone_voice(audio_path, text):
    """调用API克隆声音（使用全局配置）"""
    try:
        api_key = get_effective_api_key()
        api_url = get_effective_api_url()
        model_name = get_effective_model_name()

        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            return {
                "success": False,
                "message": "请先配置 API Key",
                "details": "可通过网页顶部「API 配置」面板输入，或修改 config.json"
            }

        if not api_url:
            return {
                "success": False,
                "message": "请先配置 API URL",
                "details": "可通过网页顶部「API 配置」面板输入"
            }

        if not model_name:
            return {
                "success": False,
                "message": "请先配置模型名称",
                "details": "请检查 config.json 中的 model_name 字段"
            }

        with open(audio_path, 'rb') as f:
            audio_data = f.read()
            audio_b64 = base64.b64encode(audio_data).decode()
        
        file_ext = Path(audio_path).suffix[1:].lower()
        audio_dataurl = f"data:audio/{file_ext};base64,{audio_b64}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        style_match = re.match(r'^\(([^)]+)\)', text)
        style_tag = style_match.group(0) if style_match else ""
        main_text = text[len(style_tag):] if style_tag else text
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": f"请用以下声音克隆说：{text}"},
                {"role": "assistant", "content": text}
            ],
            "audio": {"voice": audio_dataurl, "format": "wav"}
        }
        
        print(f"[*] 正在调用API克隆声音...")
        print(f"    API URL: {api_url}")
        print(f"    Model: {model_name}")
        print(f"    文本: {text[:100]}...")
        print(f"    音频大小: {len(audio_data)/1024:.1f} KB")
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice and "audio" in choice["message"]:
                    audio_info = choice["message"]["audio"]
                    if "data" in audio_info:
                        output_filename = generate_unique_filename("wav")
                        output_path = Path(config.get('output_dir', 'outputs')) / output_filename
                        audio_bytes = base64.b64decode(audio_info["data"])
                        with open(output_path, 'wb') as f:
                            f.write(audio_bytes)
                        
                        print(f"[OK] 声音克隆成功！文件: {output_filename}")
                        return {
                            "success": True,
                            "message": "声音克隆成功！",
                            "download_url": url_for('download_file', filename=output_filename, _external=True),
                            "preview_url": url_for('preview_file', filename=output_filename, _external=True),
                            "local_path": str(output_path.absolute()),
                            "filename": output_filename,
                            "file_size": len(audio_bytes) / 1024,
                            "sent_text": text,
                            "style_tag": style_tag,
                            "main_text": main_text
                        }
            return {"success": False, "message": "API响应格式异常", "details": str(result)[:500]}
        else:
            error_msg = response.text[:500]
            print(f"[ERR] API请求失败: {response.status_code}")
            return {"success": False, "message": f"API请求失败: {response.status_code}", "details": error_msg}
    
    except requests.exceptions.Timeout:
        return {"success": False, "message": "API请求超时", "details": "请求超时，请缩短文本长度后重试"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "API连接失败", "details": "无法连接到API服务器"}
    except Exception as e:
        return {"success": False, "message": f"处理错误: {str(e)}", "details": None}


def clone_voice_with_key(audio_path, text, request_api_key, request_api_url=''):
    """
    使用指定的 API Key 克隆声音（支持每人自带 Key）
    优先级：请求携带的 Key > 热配置 > config.json
    """
    try:
        # 确定使用的 API Key（请求携带优先）
        api_key = request_api_key
        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            api_key = get_effective_api_key()
        
        # 确定使用的 API URL（请求携带优先）
        api_url = request_api_url if request_api_url else get_effective_api_url()
        model_name = get_effective_model_name()

        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            return {"success": False, "message": "API Key 无效", "details": "请输入有效的 API Key"}

        if not api_url:
            return {"success": False, "message": "请先配置 API URL", "details": "可通过网页顶部「API 配置」面板输入"}

        if not model_name:
            return {"success": False, "message": "请先配置模型名称", "details": "请检查 config.json 中的 model_name 字段"}

        with open(audio_path, 'rb') as f:
            audio_data = f.read()
            audio_b64 = base64.b64encode(audio_data).decode()
        
        file_ext = Path(audio_path).suffix[1:].lower()
        audio_dataurl = f"data:audio/{file_ext};base64,{audio_b64}"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        style_match = re.match(r'^\(([^)]+)\)', text)
        style_tag = style_match.group(0) if style_match else ""
        main_text = text[len(style_tag):] if style_tag else text
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": f"请用以下声音克隆说：{text}"},
                {"role": "assistant", "content": text}
            ],
            "audio": {"voice": audio_dataurl, "format": "wav"}
        }
        
        masked_key = api_key[:4] + '****' + api_key[-4:] if len(api_key) > 8 else '****'
        print(f"[*] 正在调用API克隆声音...")
        print(f"    API URL: {api_url}")
        print(f"    Model: {model_name}")
        print(f"    API Key: {masked_key}")
        print(f"    文本: {text[:100]}...")
        print(f"    音频大小: {len(audio_data)/1024:.1f} KB")
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice and "audio" in choice["message"]:
                    audio_info = choice["message"]["audio"]
                    if "data" in audio_info:
                        output_filename = generate_unique_filename("wav")
                        output_path = Path(config.get('output_dir', 'outputs')) / output_filename
                        audio_bytes = base64.b64decode(audio_info["data"])
                        with open(output_path, 'wb') as f:
                            f.write(audio_bytes)
                        
                        print(f"[OK] 声音克隆成功！文件: {output_filename}")
                        return {
                            "success": True,
                            "message": "声音克隆成功！",
                            "download_url": url_for('download_file', filename=output_filename, _external=True),
                            "preview_url": url_for('preview_file', filename=output_filename, _external=True),
                            "local_path": str(output_path.absolute()),
                            "filename": output_filename,
                            "file_size": len(audio_bytes) / 1024,
                            "sent_text": text,
                            "style_tag": style_tag,
                            "main_text": main_text
                        }
            return {"success": False, "message": "API响应格式异常", "details": str(result)[:500]}
        else:
            error_msg = response.text[:500]
            print(f"[ERR] API请求失败: {response.status_code}")
            return {"success": False, "message": f"API请求失败: {response.status_code}", "details": error_msg}
    
    except requests.exceptions.Timeout:
        return {"success": False, "message": "API请求超时", "details": "请求超时，请缩短文本长度后重试"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "API连接失败", "details": "无法连接到API服务器"}
    except Exception as e:
        return {"success": False, "message": f"处理错误: {str(e)}", "details": None}


# ==================== 路由 ====================

@app.route('/')
def index():
    """主页"""
    return render_template('index.html', config=config)


@app.route('/api/hot-config', methods=['GET'])
def get_hot_config():
    """获取当前有效配置（支持多进程）"""
    with hot_config_lock:
        hot_config_data = load_hot_config()
        api_key_source = 'hot' if hot_config_data.get('api_key') else 'config'
        api_url_source = 'hot' if hot_config_data.get('api_url') else 'config'

    effective_key = get_effective_api_key()
    effective_url = get_effective_api_url()
    effective_model = get_effective_model_name()

    masked_key = ''
    if effective_key and effective_key != 'YOUR_API_KEY_HERE':
        if len(effective_key) > 8:
            masked_key = effective_key[:4] + '****' + effective_key[-4:]
        else:
            masked_key = '****'

    return jsonify({
        "success": True,
        "api_key": masked_key,
        "api_url": effective_url,
        "model_name": effective_model,
        "api_key_source": api_key_source,
        "api_url_source": api_url_source,
        "api_key_configured": bool(effective_key) and effective_key != 'YOUR_API_KEY_HERE'
    })


@app.route('/api/hot-config', methods=['POST'])
def set_hot_config():
    """热更新 API 配置（写入文件，支持多进程）"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "请求数据为空"}), 400

        updated_fields = []

        with hot_config_lock:
            hot_config_data = load_hot_config()

            if 'api_key' in data or 'apiKey' in data:
                val = data.get('api_key') or data.get('apiKey') or ''
                val = val.strip() if val else ''
                hot_config_data['api_key'] = val if val else None
                updated_fields.append('api_key')

            if 'api_url' in data or 'apiUrl' in data:
                val = data.get('api_url') or data.get('apiUrl') or ''
                val = val.strip() if val else ''
                if val.endswith('/'):
                    val = val.rstrip('/')
                hot_config_data['api_url'] = val if val else None
                updated_fields.append('api_url')

            save_hot_config_to_file(hot_config_data)

        if not updated_fields:
            return jsonify({"success": False, "message": "没有可更新的字段"}), 400

        print(f"[更新] 热更新配置: {', '.join(updated_fields)}")
        return jsonify({
            "success": True,
            "message": f"配置已更新: {', '.join(updated_fields)}，立即生效！",
            "updated_fields": updated_fields
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"更新配置失败: {str(e)}"}), 500


@app.route('/api/hot-config', methods=['DELETE'])
def reset_hot_config():
    """重置热加载配置"""
    try:
        with hot_config_lock:
            save_hot_config_to_file({'api_key': None, 'api_url': None})
        print("[更新] 热加载配置已重置")
        return jsonify({"success": True, "message": "已重置为 config.json 配置"})
    except Exception as e:
        return jsonify({"success": False, "message": f"重置配置失败: {str(e)}"}), 500


@app.route('/clone', methods=['POST'])
def clone():
    """处理声音克隆请求（支持每人自带 API Key）"""
    try:
        if 'audio_file' not in request.files:
            return jsonify({"success": False, "message": "请上传音频文件"}), 400
        
        file = request.files['audio_file']
        text = request.form.get('text', '').strip()
        
        # 获取请求中携带的 API Key 和 URL（每人各自的 Key）
        request_api_key = request.form.get('api_key', '').strip()
        request_api_url = request.form.get('api_url', '').strip()
        
        if file.filename == '':
            return jsonify({"success": False, "message": "未选择文件"}), 400
        
        if not text:
            return jsonify({"success": False, "message": "请输入要合成的文本"}), 400
        
        # 检查是否提供了 API Key（个人的或全局的）
        if not request_api_key:
            global_key = get_effective_api_key()
            if not global_key or global_key == 'YOUR_API_KEY_HERE':
                return jsonify({"success": False, "message": "请输入你的 API Key"}), 400
        
        if not allowed_file(file.filename):
            allowed = ', '.join(config.get('allowed_extensions', ['wav', 'mp3', 'ogg', 'flac']))
            return jsonify({"success": False, "message": f"不支持的文件类型，允许: {allowed}"}), 400
        
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        saved_filename = generate_unique_filename(file_ext)
        upload_path = Path('uploads') / saved_filename
        
        file.save(upload_path)
        
        file_size_mb = upload_path.stat().st_size / (1024 * 1024)
        if file_size_mb > config.get('max_file_size_mb', 50):
            upload_path.unlink()
            return jsonify({"success": False, "message": f"文件太大，最大: {config.get('max_file_size_mb', 50)}MB"}), 400
        
        # 使用带个人 Key 的克隆函数
        result = clone_voice_with_key(upload_path, text, request_api_key, request_api_url)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"success": False, "message": f"服务器错误: {str(e)}"}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """下载文件"""
    try:
        output_dir = Path(config.get('output_dir', 'outputs'))
        file_path = output_dir / filename
        
        if file_path.exists():
            if filename.endswith('.wav'):
                mime_type = 'audio/wav'
            elif filename.endswith('.mp3'):
                mime_type = 'audio/mpeg'
            elif filename.endswith('.ogg'):
                mime_type = 'audio/ogg'
            elif filename.endswith('.flac'):
                mime_type = 'audio/flac'
            else:
                mime_type = 'audio/wav'
            
            response = send_file(file_path, as_attachment=True, download_name=filename, mimetype=mime_type)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            return jsonify({"success": False, "message": "文件不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"下载错误: {str(e)}"}), 500


@app.route('/preview/<filename>')
def preview_file(filename):
    """预览音频文件"""
    try:
        output_dir = Path(config.get('output_dir', 'outputs'))
        file_path = output_dir / filename
        
        if file_path.exists():
            if filename.endswith('.wav'):
                mime_type = 'audio/wav'
            elif filename.endswith('.mp3'):
                mime_type = 'audio/mpeg'
            elif filename.endswith('.ogg'):
                mime_type = 'audio/ogg'
            elif filename.endswith('.flac'):
                mime_type = 'audio/flac'
            else:
                mime_type = 'audio/wav'
            
            response = send_file(file_path, mimetype=mime_type)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            response.headers['Accept-Ranges'] = 'bytes'
            return response
        else:
            return "文件不存在", 404
    except Exception as e:
        return f"预览错误: {str(e)}", 500


@app.route('/files')
def list_files():
    """列出所有输出文件"""
    try:
        output_dir = Path(config.get('output_dir', 'outputs'))
        files = []
        if output_dir.exists():
            for file_path in sorted(output_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
                if file_path.is_file():
                    files.append({
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "size_human": f"{file_path.stat().st_size / 1024:.1f} KB",
                        "created": datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "download_url": url_for('download_file', filename=file_path.name, _external=True),
                        "preview_url": url_for('preview_file', filename=file_path.name, _external=True)
                    })
        return jsonify({"success": True, "files": files, "total": len(files)})
    except Exception as e:
        return jsonify({"success": False, "message": f"获取文件列表失败: {str(e)}"}), 500


@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    """删除输出文件"""
    try:
        output_dir = Path(config.get('output_dir', 'outputs'))
        file_path = output_dir / filename
        if file_path.exists():
            file_path.unlink()
            return jsonify({"success": True, "message": f"文件 {filename} 已删除"})
        else:
            return jsonify({"success": False, "message": "文件不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"删除文件失败: {str(e)}"}), 500


@app.route('/health')
def health_check():
    """健康检查"""
    api_key = get_effective_api_key()
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "api_url": get_effective_api_url(),
            "model_name": get_effective_model_name(),
            "api_key_configured": bool(api_key) and api_key != 'YOUR_API_KEY_HERE',
            "port": config.get('port', 8080)
        }
    })


@app.route('/config')
def get_config():
    """获取配置信息"""
    safe_config = config.copy()
    if 'api_key' in safe_config:
        key = safe_config['api_key']
        if key and len(key) > 8:
            safe_config['api_key'] = key[:4] + '****' + key[-4:]
    return jsonify(safe_config)


# ==================== 错误处理 ====================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "请求的资源不存在"}), 404


@app.errorhandler(413)
def too_large(error):
    return jsonify({"success": False, "message": f"文件太大，最大: {config.get('max_file_size_mb', 50)}MB"}), 413


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "服务器内部错误"}), 500


# ==================== 关键：模块加载时初始化配置 ====================
# Passenger WSGI 环境中这些代码会在 import 时执行
load_config()

# 创建必要目录
try:
    Path(config.get('output_dir', 'outputs')).mkdir(exist_ok=True)
    Path('uploads').mkdir(exist_ok=True)
except:
    pass

# ==================== 主程序入口（仅直接运行时执行）====================

if __name__ == '__main__':
    cleanup_old_files()
    
    api_key = config.get('api_key', '')
    key_configured = api_key and api_key != 'YOUR_API_KEY_HERE'
    
    print("=" * 60)
    print("[TTS] MiMo 声音克隆 Web 平台")
    print("=" * 60)
    print(f"[WEB]  访问地址: http://{config.get('host', '0.0.0.0')}:{config.get('port', 8080)}")
    print(f"[DIR]  上传目录: uploads/")
    print(f"[DIR]  输出目录: {config.get('output_dir', 'outputs')}/")
    print(f"[KEY]  API Key: {'已配置' if key_configured else '[WARN] 未配置'}")
    print(f"[WEB]  API URL: {config.get('api_url', 'N/A')}")
    print(f"[PKG]  Model:   {config.get('model_name', 'N/A')}")
    print("=" * 60)
    
    app.run(
        host=config.get('host', '0.0.0.0'),
        port=config.get('port', 8080),
        debug=config.get('debug_mode', False)
    )
