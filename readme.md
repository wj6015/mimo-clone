# 🎙️ MiMo 声音克隆平台

基于小米 **MiMo-v2.5-TTS-VoiceClone** 模型的 Web 端声音克隆服务平台。上传或录制一段参考音频，输入要合成的文本，即可生成克隆语音。

![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Flask](https://img.shields.io/badge/Flask-3.x-green) ![License](https://img.shields.io/badge/License-MIT-orange)

---

## 📋 目录

- [功能特性](#功能特性)
- [适配平台](#适配平台)
- [项目结构](#项目结构)
- [快速部署](#快速部署)
- [运行管理](#运行管理)
- [Cloudflare 反代配置](#cloudflare-反代配置)
- [NAT VPS 端口说明](#nat-vps-端口说明)
- [配置说明](#配置说明)
- [维护策略](#维护策略)
- [常见问题与排查](#常见问题与排查)
- [技术架构](#技术架构)
- [安全说明](#安全说明)
- [许可证](#许可证)

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| **声音克隆** | 上传参考音频 + 输入文本 → 生成克隆语音 |
| **浏览器录音** | 支持在网页端直接录制参考音频（需 HTTPS） |
| **实时波形** | 录音时实时显示音频波形动画 |
| **录音预览** | 录制完成后可试听，不满意可重录 |
| **WAV 自动转码** | 浏览器录音（webm/m4a）自动转为 WAV 格式，兼容 API |
| **风格控制** | 8 大类、50+ 种整体风格（情绪/语调/音色/方言/角色等） |
| **细粒度标签** | 插入呼吸、停顿、颤抖、哭笑等精细控制标签 |
| **个人 API Key** | 每位用户可输入自己的 API Key，互不影响 |
| **热加载配置** | 通过网页实时修改 API Key/URL，无需重启服务 |
| **Cloudflare 反代** | 支持通过域名 + HTTPS 访问，适配 NAT VPS |
| **自动守护** | watchdog 自动检测并拉起崩溃的服务 |
| **一键部署** | `mimo.sh` 脚本集成部署、启动、监控、卸载全流程 |

---

## 🖥️ 适配平台

### 支持的操作系统（服务端）

| 系统 | 支持状态 |
|------|---------|
| Alpine Linux | ✅ 主要适配 |
| Debian / Ubuntu | ✅ |
| CentOS / RHEL | ✅ |

### 支持的浏览器（客户端）

| 浏览器 | 上传文件 | 浏览器录音 | 说明 |
|--------|---------|-----------|------|
| Chrome / Edge (桌面) | ✅ | ✅ | 需 HTTPS |
| Safari (macOS) | ✅ | ✅ | 需 HTTPS |
| Safari (iOS) | ✅ | ✅ | **iOS 唯一完全支持录音的浏览器** |
| Chrome (Android) | ✅ | ✅ | 需 HTTPS |
| Chrome (iOS) | ✅ | ⚠️ | iOS 上 Chrome 使用 WebKit 引擎，可能存在兼容性问题，建议用 Safari |
| Firefox (桌面) | ✅ | ✅ | 需 HTTPS |
| 微信内置浏览器 | ✅ | ❌ | 不支持 MediaRecorder，仅可上传文件 |
| Safari (iOS < 14.5) | ✅ | ❌ | 系统版本过低，不支持 MediaRecorder |

> **⚠️ 重要：浏览器录音功能（getUserMedia）要求 HTTPS 连接。HTTP 下无法使用录音。**

---

## 📁 项目结构
mimo-clone/ ├── app.py # Flask 后端主程序 ├── config.json # 应用配置文件（端口、API Key、模型等） ├── hot_config.json # 热加载配置文件（网页端动态修改） ├── mimo.sh # 一体化管理脚本（部署/启动/停止/卸载） ├── watchdog.sh # 守护进程脚本（自动生成） ├── requirements.txt # Python 依赖 ├── passenger_wsgi.py # Passenger WSGI 入口（部分面板使用） ├── templates/ │ └── index.html # 前端页面（HTML + CSS + JS 全内联） ├── static/ │ └── css/ │ └── style.css # 全局样式 ├── uploads/ # 用户上传的参考音频（临时存储） ├── outputs/ # 克隆生成的音频文件 ├── venv/ # Python 虚拟环境 ├── app.log # 应用运行日志 └── watchdog.log # 守护进程日志

---

## 🚀 快速部署

### 前提条件

- 一台可访问的 VPS（推荐 NAT VPS / IPv6 VPS）
- 一个有效的 MiMo TTS API Key（从 [mimo.xiaomi.com](https://mimo.xiaomi.com) 获取）
- （可选）一个域名 + Cloudflare 账号（用于 HTTPS 反代）

### 一键部署

```bash
# 1. 连接 VPS
ssh root@你的VPS地址 -p 端口

# 2. 下载管理脚本（方式一：git）
apk add git  # Alpine
git clone https://github.com/wj6015/mimo-clone.git

# 方式二：直接创建脚本（如果 git 不可用）
# 将 mimo.sh 内容粘贴到 VPS 上
vi ~/mimo.sh

# 3. 赋予执行权限
chmod +x ~/mimo-clone/mimo.sh

# 4. 首次部署（交互式，会引导你输入端口和 API Key）
cd ~/mimo-clone
./mimo.sh deploy

# 5. 启动服务
./mimo.sh start

部署过程中会交互式询问：

端口号 — 你的 NAT VPS 端口转发规则中的端口（默认 8080）
API Key — MiMo TTS 的 API Key（可留空，后续在网页端配置）

🎛️ 运行管理
所有操作通过 mimo.sh 一个脚本完成：

./mimo.sh deploy    # 首次部署（环境检查 + 安装依赖 + 配置）
./mimo.sh start     # 启动应用 + 自动守护（watchdog）
./mimo.sh stop      # 停止应用 + 守护进程
./mimo.sh restart   # 重启应用
./mimo.sh status    # 查看运行状态
./mimo.sh log       # 查看实时日志（Ctrl+C 退出）
./mimo.sh remove    # 彻底卸载（停止服务 + 删除所有文件）

运行状态示例

$ ./mimo.sh status

============================================================
  MiMo 声音克隆平台 - 运行状态
============================================================

  watchdog:  运行中
  app.py:    运行中 (PID: 1234)

  端口:      8080
  API Key:   是
  项目目录:  /root/mimo-clone
  应用日志:  /root/mimo-clone/app.log
  守护日志:  /root/mimo-clone/watchdog.log

  直连访问:  http://[你的VPS-IPv6地址]:8080
  CF 访问:   https://你的域名（需配置 Cloudflare）
