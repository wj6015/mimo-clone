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

|
 功能 
|
 说明 
|
|
------
|
------
|
|
**
声音克隆
**
|
 上传参考音频 + 输入文本 → 生成克隆语音 
|
|
**
浏览器录音
**
|
 支持在网页端直接录制参考音频（需 HTTPS） 
|
|
**
实时波形
**
|
 录音时实时显示音频波形动画 
|
|
**
录音预览
**
|
 录制完成后可试听，不满意可重录 
|
|
**
WAV 自动转码
**
|
 浏览器录音（webm/m4a）自动转为 WAV 格式，兼容 API 
|
|
**
风格控制
**
|
 8 大类、50+ 种整体风格（情绪/语调/音色/方言/角色等） 
|
|
**
细粒度标签
**
|
 插入呼吸、停顿、颤抖、哭笑等精细控制标签 
|
|
**
个人 API Key
**
|
 每位用户可输入自己的 API Key，互不影响 
|
|
**
热加载配置
**
|
 通过网页实时修改 API Key/URL，无需重启服务 
|
|
**
Cloudflare 反代
**
|
 支持通过域名 + HTTPS 访问，适配 NAT VPS 
|
|
**
自动守护
**
|
 watchdog 自动检测并拉起崩溃的服务 
|
|
**
一键部署
**
|
`mimo.sh`
 脚本集成部署、启动、监控、卸载全流程 
|

---

## 🖥️ 适配平台

### 支持的操作系统（服务端）

|
 系统 
|
 支持状态 
|
|
------
|
---------
|
|
 Alpine Linux 
|
 ✅ 主要适配 
|
|
 Debian / Ubuntu 
|
 ✅ 
|
|
 CentOS / RHEL 
|
 ✅ 
|

### 支持的浏览器（客户端）

|
 浏览器 
|
 上传文件 
|
 浏览器录音 
|
 说明 
|
|
--------
|
---------
|
-----------
|
------
|
|
 Chrome / Edge (桌面) 
|
 ✅ 
|
 ✅ 
|
 需 HTTPS 
|
|
 Safari (macOS) 
|
 ✅ 
|
 ✅ 
|
 需 HTTPS 
|
|
 Safari (iOS) 
|
 ✅ 
|
 ✅ 
|
**
iOS 唯一完全支持录音的浏览器
**
|
|
 Chrome (Android) 
|
 ✅ 
|
 ✅ 
|
 需 HTTPS 
|
|
 Chrome (iOS) 
|
 ✅ 
|
 ⚠️ 
|
 iOS 上 Chrome 使用 WebKit 引擎，可能存在兼容性问题，建议用 Safari 
|
|
 Firefox (桌面) 
|
 ✅ 
|
 ✅ 
|
 需 HTTPS 
|
|
 微信内置浏览器 
|
 ✅ 
|
 ❌ 
|
 不支持 MediaRecorder，仅可上传文件 
|
|
 Safari (iOS < 14.5) 
|
 ✅ 
|
 ❌ 
|
 系统版本过低，不支持 MediaRecorder 
|

> **⚠️ 重要：浏览器录音功能（getUserMedia）要求 HTTPS 连接。HTTP 下无法使用录音。**

---

## 📁 项目结构
mimo-clone/ ├── app.py # Flask 后端主程序 ├── config.json # 应用配置文件（端口、API Key、模型等） ├── hot_config.json # 热加载配置文件（网页端动态修改） ├── mimo.sh # 一体化管理脚本（部署/启动/停止/卸载） ├── watchdog.sh # 守护进程脚本（自动生成） ├── requirements.txt # Python 依赖 ├── passenger_wsgi.py # Passenger WSGI 入口（部分面板使用） ├── templates/ │ └── index.html # 前端页面（HTML + CSS + JS 全内联） ├── static/ │ └── css/ │ └── style.css # 全局样式 ├── uploads/ # 用户上传的参考音频（临时存储） ├── outputs/ # 克隆生成的音频文件 ├── venv/ # Python 虚拟环境 ├── app.log # 应用运行日志 └── watchdog.log # 守护进程日志

text



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

bash


./mimo.sh deploy    # 首次部署（环境检查 + 安装依赖 + 配置）
./mimo.sh start     # 启动应用 + 自动守护（watchdog）
./mimo.sh stop      # 停止应用 + 守护进程
./mimo.sh restart   # 重启应用
./mimo.sh status    # 查看运行状态
./mimo.sh log       # 查看实时日志（Ctrl+C 退出）
./mimo.sh remove    # 彻底卸载（停止服务 + 删除所有文件）
运行状态示例
text


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
守护机制（watchdog）
watchdog 每 30 秒 检查一次 app.py 是否存活
如果 app.py 崩溃或被意外终止，watchdog 会在 30 秒内自动拉起
开机自启：系统重启后 watchdog 自动启动（通过 ~/.profile）
守护日志：watchdog.log 记录所有拉起事件
☁️ Cloudflare 反代配置
如果你的 VPS 没有公网 IPv4（NAT VPS），或希望通过域名 + HTTPS 访问，可以使用 Cloudflare 反代。

流量走向
text


用户浏览器 → HTTPS(443) → Cloudflare CDN → HTTP(你的端口) → 你的 VPS
配置步骤
第 1 步：添加 DNS 记录
进入 Cloudflare Dashboard → 你的域名 → DNS

Table


字段	值
类型	AAAA
名称	你的子域名（如 mi，对应 mi.example.com）
值	你的 VPS IPv6 地址（如 2a12:de40:9::2ab:b）
代理状态	开启（橙色云朵 ☁️）
第 2 步：SSL/TLS 设置
进入 Cloudflare → SSL/TLS → 概述

Table


设置项	值	说明
加密模式	Flexible	源站只监听 HTTP，不需要 HTTPS 证书
最低 TLS 版本	TLS 1.2	推荐
⚠️ 不要选择 Full 或 Full (Strict)，因为源站没有配置 SSL 证书，选择 Full 会导致 502/522 错误。

第 3 步：启用 IPv6 兼容
进入 Cloudflare → Network

Table


设置项	值
IPv6 Compatibility	开启 ✅
如果你的源站只有 IPv6 地址，必须开启此选项，否则 Cloudflare 无法连接源站。

第 4 步：源站端口设置（非标准端口时）
Cloudflare 仅支持以下端口：

Table


协议	支持的端口
HTTP	80, 8080, 8880, 2052, 2082, 2086, 2095
HTTPS	443, 2053, 2083, 2087, 2096
如果你的端口是 80 或 8080：无需额外配置，直接访问 https://你的域名。

如果你的端口不在以上列表中（如 30619）：需要创建 Origin Rule。

进入 Cloudflare → Rules → Origin Rules → Create rule

Table


字段	值
Rule name	forward-to-你的端口
When incoming requests match	All incoming requests
Then	Set origin port → 你的端口号
点击 Deploy，等待 1-2 分钟生效。

验证
bash


# 直连 IPv6 测试
curl -6 http://[你的VPS-IPv6地址]:你的端口

# Cloudflare 域名测试
curl https://你的域名
🔌 NAT VPS 端口说明
什么是 NAT VPS
NAT VPS 是一种共享公网 IPv4 地址的 VPS，通过端口转发实现外部访问。通常：

内部有私有 IPv4（如 10.x.x.x）
有一个或多个公网 IPv6 地址
提供有限的端口转发（通常 2-20 个端口）
端口转发设置
在 VPS 后台设置端口转发规则：

text


内部端口: 8080  →  转发  →  外部端口: 8080
建议内外端口设置一致，避免混淆。

访问方式
Table


方式	地址格式	前提条件
IPv6 直连	http://[2a12:de40:9::xxx]:8080	你的网络支持 IPv6
Cloudflare	https://你的域名	已配置 CF 反代
IPv6 地址必须用方括号 [] 包裹，且端口号前加冒号 :。

如何检查本地是否有 IPv6
访问 https://test-ipv6.com，如果显示 IPv6 地址则支持。

大多数 4G/5G 移动网络和现代宽带默认支持 IPv6。

⚙️ 配置说明
config.json
json


{
    "api_url": "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
    "model_name": "mimo-v2.5-tts-voiceclone",
    "api_key": "tp-你的API密钥",
    "port": 8080,
    "host": "::",
    "max_file_size_mb": 50,
    "allowed_extensions": ["wav", "mp3", "ogg", "flac", "webm", "m4a"],
    "output_dir": "outputs",
    "auto_cleanup_hours": 24,
    "default_text": "你好，这是声音克隆测试",
    "debug_mode": false
}
Table


字段	说明	默认值
api_url	MiMo TTS API 地址	https://token-plan-cn.xiaomimimo.com/v1/chat/completions
model_name	模型名称	mimo-v2.5-tts-voiceclone
api_key	你的 API Key	空（需手动配置）
port	监听端口	8080
host	监听地址（:: = IPv4 + IPv6 全部接口）	::
max_file_size_mb	上传文件大小限制（MB）	50
allowed_extensions	允许上传的音频格式	["wav", "mp3", "ogg", "flac", "webm", "m4a"]
output_dir	克隆输出目录	outputs
auto_cleanup_hours	自动清理过期输出文件（小时）	24
default_text	页面默认文本	你好，这是声音克隆测试
debug_mode	调试模式	false
热加载配置
通过网页顶部的 API 配置 面板可以实时修改 API Key 和 API URL，无需重启服务。

热加载配置存储在 hot_config.json 中，优先级高于 config.json：

text


热加载配置（hot_config.json）> 配置文件（config.json）
如需重置为 config.json 的配置，在网页面板点击 恢复默认 即可。

🔧 维护策略
日常运维
bash


# 查看运行状态
./mimo.sh status

# 查看实时日志
./mimo.sh log

# 重启应用
./mimo.sh restart

# 清理旧的输出文件（也可在 config.json 中设置自动清理）
rm -rf ~/mimo-clone/outputs/*
日志文件
Table


日志文件	内容
app.log	应用运行日志（请求记录、API 调用、错误信息）
watchdog.log	守护进程日志（自动拉起记录）
自动清理
config.json 中的 auto_cleanup_hours 控制输出文件的自动清理周期。应用每次启动时会清理超过该时间的文件。默认 24 小时。

更新项目
bash


# 停止服务
./mimo.sh stop

# 更新代码
cd ~/mimo-clone
git pull

# 重新部署（不会覆盖 config.json 中的自定义配置）
./mimo.sh deploy

# 启动
./mimo.sh start
备份
建议定期备份 config.json：

bash


cp ~/mimo-clone/config.json ~/config.json.bak
❓ 常见问题与排查
1. 浏览器录音提示"麦克风权限被拒绝"
原因：浏览器未授权麦克风权限，或使用 HTTP 访问。

解决：

确保使用 HTTPS 访问（https://你的域名）
点击浏览器地址栏左侧的 🔒 图标 → 网站设置 → 允许麦克风
Chrome：设置 → 隐私与安全 → 网站设置 → 麦克风 → 允许你的域名
2. iOS Chrome 无法录音
原因：iOS 上的 Chrome 使用 WebKit 引擎，navigator.mediaDevices 在某些版本中不可用。

解决：

使用 Safari 浏览器访问（推荐，iOS 上唯一完全支持录音的浏览器）
或使用「上传文件」功能
3. 克隆后提示"API请求失败: 400 - Unsupported audio.voice source format"
原因：上传的音频格式不被 API 支持（如原始 webm/m4a 格式）。

解决：

浏览器录音功能已内置 WAV 自动转码，正常流程不会遇到此问题
如果是手动上传文件，确保格式为 WAV 或 MP3
4. 克隆后提示"网络错误" / "Failed to fetch"
原因：通常是 Cloudflare 超时或网络中断。

排查步骤：

bash


# 1. 检查应用是否在运行
./mimo.sh status

# 2. 检查应用日志中的错误
tail -50 ~/mimo-clone/app.log

# 3. 绕过 Cloudflare 直连测试
curl -X POST http://[::1]:8080/clone \
  -F "audio_file=@/tmp/test.wav" \
  -F "text=你好" \
  -F "api_key=你的Key" \
  --max-time 180
解决：

如果直连正常，问题是 Cloudflare 超时 → 缩短 API 超时时间
如果直连也失败，检查 VPS 网络和 API Key
5. Cloudflare 报错 "502 Bad Gateway" / "Host Error"
原因：Cloudflare 无法连接源站。

排查清单：

Table


检查项	正确设置
DNS AAAA 记录	指向正确的 IPv6 地址，开启橙色云朵
SSL/TLS	设为 Flexible（不是 Full）
IPv6 Compatibility	开启
源站端口	如果是非标准端口，需创建 Origin Rule
VPS 应用	确认 ./mimo.sh status 显示运行中
6. Cloudflare 报错 "522 Connection Timed Out"
原因：Cloudflare 连接源站超时。

解决：

确认 VPS 防火墙放行了对应端口
确认 VPS 应用正在运行
如果使用 Origin Rule，确认规则已 Deploy
7. 页面能打开，但点击克隆后一直转圈无反应
原因：浏览器请求被本地代理（VPN/代理软件）拦截。

排查：

按 F12 打开开发者工具 → Network 标签
查看 /clone 请求的 Status Code
如果显示 503 Service Unavailable 且 Remote Address 是 127.0.0.1:xxxx，说明走了本地代理
解决：

在代理软件中添加直连规则，让 VPS IP 绕过代理：
text


# Clash
- IP-CIDR6,2a12:de40:9::/48,DIRECT
或临时关闭代理后访问
8. 应用崩溃后无法自动恢复
原因：watchdog 未运行或配置异常。

解决：

bash


# 检查 watchdog 状态
ps aux | grep watchdog

# 如果 watchdog 没运行，重新启动
./mimo.sh start

# 查看 watchdog 日志
cat ~/mimo-clone/watchdog.log
9. VPS 内存不足导致应用异常
症状：克隆操作偶尔失败，日志中出现连接错误。

排查：

bash


free -m
⚠️ NAT VPS 的 free -m 显示的是宿主机内存，不代表你的 VPS 实际占用。 你的 VPS 进程通常只占用约 20-50MB 内存，正常使用无需担心。

解决：

如果确实内存紧张，重启 VPS 即可释放
watchdog 会自动在重启后拉起应用
10. port 8080 提示端口被占用
bash


# 查看占用端口的进程
netstat -tlnp | grep 8080

# 杀掉占用进程
kill -9 <PID>
11. 录音转换 WAV 时卡住
原因：录音时浏览器 AudioContext 异常。

解决：

刷新页面重试
如果持续出现，使用「上传文件」功能替代
🏗️ 技术架构
text


┌─────────────┐     HTTPS (443)      ┌──────────────────┐
│  用户浏览器   │ ──────────────────→  │   Cloudflare CDN  │
│ (Mac/iOS/   │                       │   (反向代理)       │
│  Android/PC)│                       └────────┬─────────┘
└─────────────┘                                │ HTTP
                                               ↓
                                    ┌──────────────────┐
                                    │  NAT VPS (:8080)  │
                                    │                  │
                                    │  ┌────────────┐  │
                                    │  │  Flask 应用  │  │
                                    │  │  (app.py)   │  │
                                    │  └──────┬─────┘  │
                                    │         │         │
                                    │  ┌──────┴─────┐  │
                                    │  │  watchdog   │  │
                                    │  │  (守护进程)  │  │
                                    │  └────────────┘  │
                                    └────────┬─────────┘
                                             │ HTTPS
                                             ↓
                                  ┌──────────────────────┐
                                  │  MiMo TTS API 服务    │
                                  │  (小米云端)           │
                                  └──────────────────────┘
前端技术
HTML5 + CSS3 + 原生 JavaScript（无框架依赖）
MediaRecorder API — 浏览器录音
Web Audio API — 实时波形可视化
Fetch API — 与后端通信
AudioContext — 录音格式自动转码（webm/m4a → WAV）
后端技术
Python 3.8+ + Flask
requests — 调用 MiMo TTS API
纯 WSGI 服务，无需 Nginx/Apache
录音格式兼容
Table


浏览器	录制格式	存储格式	转码方式
Chrome / Edge	webm	wav	前端 AudioContext 自动转码
Firefox	webm	wav	前端 AudioContext 自动转码
Safari (iOS/macOS)	m4a	wav	前端 AudioContext 自动转码
不支持 MediaRecorder 的浏览器	—	—	仅支持上传文件
🔒 安全说明
API Key 安全：前端页面不会明文显示 API Key，仅显示脱敏版本（如 tp-a****v0w）
个人 Key 隔离：每位用户的个人 API Key 仅在当次请求中使用，不会被存储或共享
HTTPS：通过 Cloudflare 反代强制 HTTPS，保障传输安全
文件清理：上传和输出文件默认 24 小时后自动清理
访问认证（建议）：如果需要，可在 Cloudflare 层面添加 Access 认证，限制访问人群
📄 许可证
本项目基于 MIT 许可证开源。

声音克隆技术请合法合规使用，确保你有权使用上传的音频素材。

🙏 致谢
小米 MiMo — 提供 TTS 声音克隆 API
Flask — Web 框架
Cloudflare — CDN 与反向代理
⚠️ 免责声明：本项目仅供学习和技术研究使用。请确保遵守相关法律法规，不得将声音克隆技术用于欺诈、冒充他人等非法用途。
