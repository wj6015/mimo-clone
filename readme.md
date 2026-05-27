```markdown
# 🎤 MiMo 声音克隆 Web 平台

基于小米 **MiMo-v2.5-TTS-VoiceClone** 模型的声音克隆 Web 服务平台。

支持声音克隆、多种风格标签、细粒度语音控制标签，适合快速搭建在线 TTS 声音克隆服务。

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.x-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ 功能特性

- 🎤 **声音克隆**：上传参考音频，克隆声音说出任意文本
- 🎨 **整体风格**：支持多种风格标签（情绪、语调、音色、方言、角色扮演、唱歌等）
- 🎯 **细粒度控制**：支持插入呼吸、停顿、哭笑、颤抖等精细控制标签
- ⚡ **热加载配置**：API Key 和 API URL 可通过网页实时切换，无需重启
- 👥 **多人并发**：支持每个用户使用自己的 API Key，互不影响
- 🎧 **在线预览**：克隆完成后可直接在网页上播放和下载
- 📱 **响应式设计**：支持 PC 和移动端访问

---

## 📁 项目结构

```
mimo-voice-clone/
├── app.py                  # Flask 主应用
├── passenger_wsgi.py       # WSGI 入口文件（DirectAdmin 部署用）
├── requirements.txt        # Python 依赖列表
├── .htaccess               # Apache 路由配置（DirectAdmin 部署用）
├── run.sh                  # 本地启动脚本
├── config.json             # 配置文件（首次运行自动生成）
├── hot_config.json         # 热加载配置（运行时自动生成）
├── README.md               # 项目说明
├── LICENSE                 # 开源协议
├── .gitignore              # Git 忽略规则
├── templates/
│   └── index.html          # 前端页面
├── static/
│   └── css/
│       └── style.css       # 样式文件
├── uploads/                # 上传的音频文件（运行时使用）
└── outputs/                # 生成的克隆音频（运行时使用）
```

---

## 🚀 快速开始（本地运行）

### 环境要求

- Python 3.8+
- FFmpeg（音频处理，可选）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/wj6015/mimo-clone.git
cd mimo-clone

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python app.py
# 或使用启动脚本（Linux/Mac）
chmod +x run.sh && ./run.sh
```

浏览器打开 `http://localhost:8080` 即可访问。

---

## 🌐 DirectAdmin 面板部署指南

> 适用于使用 DirectAdmin 面板的虚拟主机（如 freecloud.ltd 等提供 Python 环境的主机）

### 前置条件

- 已购买支持 Python 的 DirectAdmin 虚拟主机
- 已绑定域名（如 `your-domain.com`）
- 有 DirectAdmin 登录账号和密码

---

### 第一步：登录 DirectAdmin 面板

```
访问：https://your-domain.com:2222
或：https://your-server-ip:2222
```

使用你的 DirectAdmin 用户名和密码登录。登录后在首页可以看到你的用户名（后续步骤需要用到）。

---

### 第二步：进入 Python 应用管理

在 DirectAdmin 面板中找到：

```
高级功能 → Python 应用（Setup Python App）
或：Extra Features → Setup Python App
或：Advanced Features → Python Selector
```

---

### 第三步：创建 Python 应用

点击 **Create Application**，填写以下内容：

| 字段 | 填写内容 |
|------|---------|
| **Python 版本** | 选择 3.8 或更高（推荐 3.11） |
| **Application root** | `mimo-clone` |
| **Application URL** | `/`（独立域名时）或 `mimo-clone`（子目录时） |
| **Application startup file** | `passenger_wsgi.py` |
| **Application Entry point** | `application` |
| **Environment variables** | 不填，跳过 |

点击 **Create**。

> ⚠️ **注意**：`Application root` 不能填 `public_html` 本身，必须是子文件夹名。`public_html` 已被占用会报错。

创建成功后，面板会显示类似信息：

```
source /home/your_username/virtualenv/mimo-clone/3.11/bin/activate && cd /home/your_username/mimo-clone
```

**记录下这两个关键路径：**

```
Python 路径：/home/your_username/virtualenv/mimo-clone/3.11/bin/python
应用目录：  /home/your_username/mimo-clone
```

---

### 第四步：上传项目文件

进入 DirectAdmin 的 **文件管理器（File Manager）**，导航到：

```
/home/your_username/mimo-clone/
```

上传以下文件和文件夹：

```
✅ app.py
✅ passenger_wsgi.py
✅ .htaccess
✅ requirements.txt
✅ templates/         （整个文件夹，包含 index.html）
✅ static/            （整个文件夹，包含 css/style.css）
```

**创建空文件夹：**

```
uploads/
outputs/
```

> 💡 **提示**：如果面板支持 ZIP 上传，可以先将所有文件打包成 zip，上传后在文件管理器中解压。
>
> ⚠️ **重要**：确保文件在 `/home/your_username/mimo-clone/` 目录下，而不是 `public_html/mimo-clone/`。这两个路径是不同的！面板创建应用时生成的目录是前者。

---

### 第五步：修改 .htaccess 文件

用文件管理器打开：

```
/home/your_username/mimo-clone/.htaccess
```

将内容修改为（替换 `your_username` 为你的实际 DirectAdmin 用户名）：

```apache
PassengerAppRoot /home/your_username/mimo-clone
PassengerBaseURI /
PassengerPython /home/your_username/virtualenv/mimo-clone/3.11/bin/python
PassengerAppType wsgi
StartupFile passenger_wsgi.py
```

> ⚠️ **关键**：`PassengerPython` 的路径必须和第三步中面板显示的 Python 路径完全一致！

保存文件。

---

### 第六步：安装 Python 依赖

回到 Python 应用管理页面，点击你创建的应用名进入详情页。

找到 **"execute python script"** 功能区域，在输入框中输入：

```
-m pip install flask requests werkzeug pydub
```

点击 **Run Script**。

等待安装完成，输出中应显示 `Successfully installed ...`。

> ⚠️ **注意**：不要使用 "run pip install" 旁边的输入框直接输入包名，那个输入框是填写 `requirements.txt` 文件路径用的。如果要用那个输入框，应填写：`/home/your_username/mimo-clone/requirements.txt`

---

### 第七步：检查文件权限

在文件管理器中，确认以下文件夹有写入权限（通常 755）：

```
/home/your_username/mimo-clone/uploads/
/home/your_username/mimo-clone/outputs/
```

如果权限不对，右键文件夹 → 属性/权限 → 设置为 755。

---

### 第八步：重启应用并访问

在 Python 应用详情页点击 **Restart** 按钮。

然后在浏览器访问：

```
https://your-domain.com
```

---

### 第九步：配置 API Key

#### 方式一：通过网页配置（推荐）

1. 打开网页，展开顶部「API 配置」面板
2. 输入 API URL 和 API Key
3. 点击「保存并生效」

#### 方式二：通过文件配置

在服务器上创建或编辑 `config.json` 文件（和 `app.py` 同目录）：

```json
{
    "api_url": "https://token-plan-cn.xiaomimimo.com/v1/chat/completions",
    "model_name": "mimo-v2.5-tts-voiceclone",
    "api_key": "你的API_KEY",
    "port": 8080,
    "host": "0.0.0.0",
    "max_file_size_mb": 50,
    "allowed_extensions": ["wav", "mp3", "ogg", "flac"],
    "output_dir": "outputs",
    "auto_cleanup_hours": 24,
    "default_text": "你好，这是声音克隆测试",
    "debug_mode": false
}
```

保存后重启应用使配置生效。

---

## 📖 使用说明

### 声音克隆流程

1. **上传参考音频**：上传一个音频文件作为声音参考（支持 WAV、MP3、OGG、FLAC）
2. **选择整体风格**（可选）：选择情绪、语调、方言等风格标签
3. **输入文本**：输入想要克隆声音说出的文字
4. **插入控制标签**（可选）：在文本中插入 `[吸气]`、`[停顿]`、`[笑]` 等标签
5. **填写 API Key**：输入你的 API Key（或留空使用管理员配置的默认 Key）
6. **点击克隆**：等待生成完成，在线播放或下载

### 多人使用

| 用户操作 | 结果 |
|---------|------|
| 填了自己的 API Key | ✅ 使用自己的 Key 克隆 |
| 没填 Key，管理员配了全局 Key | ✅ 使用管理员的 Key 克隆 |
| 没填 Key，管理员也没配 | ❌ 提示错误，需要输入 Key |

### 风格标签使用说明

#### 整体风格（添加在文本开头）

| 分类 | 示例 |
|------|------|
| 基础情绪 | `(开心)` `(悲伤)` `(愤怒)` `(平静)` `(惊讶)` |
| 复合情绪 | `(怅然)` `(欣慰)` `(无奈)` `(愧疚)` `(动情)` |
| 整体语调 | `(温柔)` `(高冷)` `(活泼)` `(慵懒)` `(俏皮)` |
| 音色定位 | `(磁性)` `(清亮)` `(甜美)` `(沙哑)` `(空灵)` |
| 人设腔调 | `(御姐音)` `(正太音)` `(大叔音)` `(夹子音)` |
| 方言 | `(东北话)` `(四川话)` `(粤语)` `(河南话)` |
| 角色扮演 | `(孙悟空)` `(林黛玉)` |
| 唱歌 | `(唱歌)歌词内容` |

#### 细粒度标签（插入在文本中间）

| 分类 | 标签 |
|------|------|
| 语速节奏 | `[吸气]` `[深呼吸]` `[叹气]` `[停顿]` `[语速加快]` `[语速放慢]` |
| 情绪状态 | `[紧张]` `[激动]` `[委屈]` `[小声]` `[害怕]` `[撒娇]` |
| 语音特征 | `[颤抖]` `[鼻音]` `[气声]` `[沙哑]` `[破音]` `[变调]` |
| 哭笑表达 | `[笑]` `[大笑]` `[冷笑]` `[抽泣]` `[哽咽]` `[咳嗽]` |

#### 示例

```
(温柔)[吸气]你好，[停顿]欢迎使用MiMo声音克隆服务。[轻笑]
```

```
(东北话)哎呀妈呀，[大笑]这也太好玩了吧！
```

```
(唱歌)让我们荡起双桨，小船儿推开波浪
```

---

## 🔧 常见问题排查

### 500 Internal Server Error

**原因**：通常是文件路径或权限问题。

**排查步骤**：

1. 检查 `.htaccess` 中的路径是否正确
2. 确认 `passenger_wsgi.py` 和 `app.py` 在同一目录下
3. 确认 `uploads/` 和 `outputs/` 文件夹存在且有写入权限
4. 查看 DirectAdmin 错误日志获取详细信息

### ModuleNotFoundError

**原因**：Python 依赖未安装。

**解决**：在 Python 应用页面使用 execute python script 安装依赖：

```
-m pip install flask requests werkzeug pydub
```

### 热加载配置不生效

**原因**：Passenger 多进程环境下内存变量不共享。

**说明**：当前版本已使用文件存储（`hot_config.json`）解决此问题。如果仍不生效，建议直接修改服务器上的 `config.json` 文件后重启应用。

### 请求频率限制（429 错误）

**原因**：API 请求过于频繁。

**解决**：
1. 使用自己的 API Key（不要共享）
2. 等待几分钟后重试
3. 升级 API 套餐

### 音频无法播放

**原因**：浏览器缓存或 URL 路径问题。

**解决**：清除浏览器缓存后重试。

---

## 🛠️ API 接口说明

### 健康检查

```
GET /health
```

### 获取配置

```
GET /api/hot-config
```

### 更新配置（热加载）

```
POST /api/hot-config
Content-Type: application/json

{
    "api_key": "your-api-key",
    "api_url": "https://your-api-url/v1/chat/completions"
}
```

### 重置配置

```
DELETE /api/hot-config
```

### 声音克隆

```
POST /clone
Content-Type: multipart/form-data

字段：
- audio_file: 音频文件（必填）
- text: 要合成的文本（必填）
- api_key: API Key（可选，留空使用全局配置）
- api_url: API URL（可选，留空使用全局配置）
```

---

## 📋 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.8+ | 后端语言 |
| Flask 2.x | Web 框架 |
| Requests | HTTP 请求库 |
| PyDub | 音频处理（可选） |
| MiMo-v2.5-TTS-VoiceClone | 小米声音克隆模型 |

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

---

## ⚠️ 免责声明

- 请确保你有权限使用上传的参考音频
- 声音克隆技术请合法合规使用，请勿用于欺诈、冒充他人等非法用途
- 本项目仅供学习和研究使用，使用者需自行承担法律责任

---

## 🙏 致谢

- [小米 AI 开放平台](https://ai.xiaomi.com/) - 提供 MiMo TTS API
- [Flask](https://flask.palletsprojects.com/) - Python Web 框架

