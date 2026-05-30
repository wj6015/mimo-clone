#!/bin/bash
# ============================================================
#  MiMo 声音克隆平台 - 一体化管理脚本
#  适用系统：Alpine Linux / Debian / CentOS
#  用法：./mimo.sh [deploy|start|stop|restart|status|log|remove]
# ============================================================

set -e

# ==================== 常量定义 ====================
PROJECT_DIR="$HOME/mimo-clone"
VENV_DIR="$PROJECT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python3"
VENV_PIP="$VENV_DIR/bin/pip"
CONFIG_FILE="$PROJECT_DIR/config.json"
APP_LOG="$PROJECT_DIR/app.log"
WATCHDOG_SCRIPT="$PROJECT_DIR/watchdog.sh"
WATCHDOG_LOG="$PROJECT_DIR/watchdog.log"
REPO_URL="https://github.com/wj6015/mimo-clone.git"
PROFILE_FILE="$HOME/.profile"
APP_NAME="MiMo 声音克隆平台"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ==================== 工具函数 ====================

info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERR]${NC} $1"; }
divider() { echo -e "${CYAN}============================================================${NC}"; }

# 检查 app.py 是否在运行
is_app_running() {
    pgrep -f "python3 app.py" > /dev/null 2>&1
}

# 检查 watchdog 是否在运行
is_watchdog_running() {
    pgrep -f "watchdog.sh" > /dev/null 2>&1
}

# 检测系统类型
detect_os() {
    if [ -f /etc/alpine-release ]; then
        echo "alpine"
    elif [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "centos"
    else
        echo "unknown"
    fi
}

# 安装系统包
install_packages() {
    local os=$(detect_os)
    info "检测到系统: $os"
    
    case "$os" in
        alpine)
            apk update
            apk add python3 py3-pip python3-dev git curl
            ;;
        debian)
            apt update
            apt install -y python3 python3-pip python3-venv git curl
            ;;
        centos)
            yum install -y python3 python3-pip git curl
            ;;
        *)
            error "未知系统，请手动安装 python3, git, curl"
            exit 1
            ;;
    esac
    success "系统依赖安装完成"
}

# ==================== deploy 命令 ====================

cmd_deploy() {
    divider
    echo -e "${CYAN}  $APP_NAME - 首次部署${NC}"
    divider
    echo ""

    # ------ 1. 交互式输入端口 ------
    echo -e "${YELLOW}【端口说明】${NC}"
    echo "  请输入你的 NAT VPS 端口转发规则中的端口号。"
    echo ""
    echo -e "${YELLOW}【Cloudflare 反代提示】${NC}"
    echo "  Cloudflare 支持的端口："
    echo "  HTTP:  80, 8080, 8880, 2052, 2082, 2086, 2095"
    echo "  HTTPS: 443, 2053, 2083, 2087, 2096"
    echo "  建议使用 8080，无需额外配置 Origin Rule。"
    echo "  其他端口需要在 Cloudflare → Rules → Origin Rules 中设置转发。"
    echo ""
    read -p "请输入端口号（回车默认 8080）: " USER_PORT
    local PORT=${USER_PORT:-8080}

    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
        error "端口号必须是 1-65535 之间的数字"
        exit 1
    fi
    success "端口设置为: $PORT"

    # ------ 2. 交互式输入 API Key ------
    echo ""
    echo -e "${YELLOW}【API Key 说明】${NC}"
    echo "  请从 https://mimo.xiaomi.com 获取你的 TTS API Key。"
    echo "  格式类似: tp-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    echo "  留空可后续在网页端配置。"
    echo ""
    read -p "请输入 API Key（留空跳过）: " USER_API_KEY
    local API_KEY=${USER_API_KEY:-""}

    if [ -n "$API_KEY" ]; then
        success "API Key 已设置"
    else
        warn "API Key 为空，可稍后在网页端配置"
    fi

    echo ""

    # ------ 3. 安装系统依赖 ------
    info "安装系统依赖..."
    install_packages

    # ------ 4. 克隆/更新项目 ------
    info "获取项目代码..."
    if [ -d "$PROJECT_DIR" ]; then
        warn "项目目录已存在，更新代码..."
        cd "$PROJECT_DIR"
        git pull 2>/dev/null || warn "更新失败，使用现有代码"
    else
        git clone "$REPO_URL" "$PROJECT_DIR"
    fi
    success "项目代码就绪"

    # ------ 5. 创建虚拟环境 ------
    info "创建 Python 虚拟环境..."
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
    fi
    success "虚拟环境就绪"

    # ------ 6. 安装依赖 ------
    info "安装 Python 依赖（首次较慢）..."
    "$VENV_PIP" install --upgrade pip > /dev/null 2>&1
    "$VENV_PIP" install -r "$PROJECT_DIR/requirements.txt"
    success "依赖安装完成"

    # ------ 7. 创建目录 ------
    mkdir -p "$PROJECT_DIR/uploads" "$PROJECT_DIR/outputs"
    success "目录创建完成"

    # ------ 8. 生成 config.json ------
    info "生成配置文件..."
    "$VENV_PYTHON" -c "
import json
config = {
    'api_url': 'https://token-plan-cn.xiaomimimo.com/v1/chat/completions',
    'model_name': 'mimo-v2.5-tts-voiceclone',
    'api_key': '$API_KEY',
    'port': $PORT,
    'host': '::',
    'max_file_size_mb': 50,
    'allowed_extensions': ['wav', 'mp3', 'ogg', 'flac', 'webm', 'm4a'],
    'output_dir': 'outputs',
    'auto_cleanup_hours': 24,
    'default_text': '你好，这是声音克隆测试',
    'debug_mode': False
}
with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=4, ensure_ascii=False)
print('OK')
"
    success "配置文件已生成: port=$PORT"

    # ------ 9. 防火墙放行 ------
    if command -v ip6tables > /dev/null 2>&1; then
        ip6tables -I INPUT -p tcp --dport "$PORT" -j ACCEPT 2>/dev/null || true
        success "防火墙已放行端口 $PORT"
    fi

    # ------ 10. 开机自启 ------
    sed -i '/mimo-clone/d' "$PROFILE_FILE" 2>/dev/null || true
    cat >> "$PROFILE_FILE" << AUTOEOF

# MiMo 声音克隆平台自启动
if [ -f "$WATCHDOG_SCRIPT" ] && ! pgrep -f "watchdog.sh" > /dev/null 2>&1; then
    nohup bash "$WATCHDOG_SCRIPT" >> "$WATCHDOG_LOG" 2>&1 &
fi
AUTOEOF
    success "开机自启已配置"

    # ------ 完成 ------
    echo ""
    divider
    echo -e "${GREEN}  ✅ 部署完成！${NC}"
    divider
    echo ""
    echo -e "  下一步：${CYAN}./mimo.sh start${NC}"
    echo ""
    echo -e "  Cloudflare 配置指引："
    echo "  ① DNS: 添加 AAAA 记录指向你的 VPS IPv6 地址，开启橙色云朵"
    echo "  ② SSL/TLS: 设置为 Flexible"
    if [[ "$PORT" != "80" && "$PORT" != "443" && "$PORT" != "8080" && \
          "$PORT" != "2053" && "$PORT" != "2083" && "$PORT" != "2087" && \
          "$PORT" != "2096" && "$PORT" != "8880" && "$PORT" != "2052" && \
          "$PORT" != "2082" && "$PORT" != "2086" && "$PORT" != "2095" ]]; then
        echo "  ③ Origin Rule: Rules → Origin Rules → Set origin port → $PORT"
    fi
    echo ""
}

# ==================== start 命令 ====================

cmd_start() {
    divider
    echo -e "${CYAN}  $APP_NAME - 启动${NC}"
    divider

    # 检查项目
    if [ ! -d "$PROJECT_DIR" ]; then
        error "项目未部署，请先执行: ./mimo.sh deploy"
        exit 1
    fi

    # 杀掉旧进程
    pkill -f "watchdog.sh" 2>/dev/null || true
    pkill -f "python3 app.py" 2>/dev/null || true
    sleep 1

    # 创建 watchdog 脚本
    cat > "$WATCHDOG_SCRIPT" << 'WATCHDOG_EOF'
#!/bin/bash
PROJECT_DIR="$HOME/mimo-clone"
VENV_PYTHON="$PROJECT_DIR/venv/bin/python3"
APP_LOG="$PROJECT_DIR/app.log"
WLOG="$PROJECT_DIR/watchdog.log"

log_msg() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$WLOG"
}

log_msg "watchdog 已启动"

while true; do
    if ! pgrep -f "python3 app.py" > /dev/null 2>&1; then
        log_msg "应用未运行，正在重启..."
        cd "$PROJECT_DIR"
        nohup "$VENV_PYTHON" app.py >> "$APP_LOG" 2>&1 &
        NEW_PID=$!
        log_msg "重启完成，PID: $NEW_PID"
        sleep 5
        if kill -0 $NEW_PID 2>/dev/null; then
            log_msg "确认存活 ✅"
        else
            log_msg "重启失败 ❌"
        fi
    fi
    sleep 30
done
WATCHDOG_EOF
    chmod +x "$WATCHDOG_SCRIPT"

    # 清空日志
    > "$WATCHDOG_LOG"

    # 启动 watchdog（它会自动启动 app.py）
    nohup bash "$WATCHDOG_SCRIPT" >> "$WATCHDOG_LOG" 2>&1 &
    local WD_PID=$!

    # 等待启动
    info "等待应用启动..."
    sleep 5

    # 验证
    if is_app_running && is_watchdog_running; then
        local PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['port'])" 2>/dev/null || echo "?")
        echo ""
        success "$APP_NAME 已启动"
        echo ""
        echo -e "  watchdog PID: ${WD_PID}"
        echo -e "  端口: ${PORT}"
        echo -e "  日志: ${APP_LOG}"
        echo ""
    else
        error "启动失败，请查看日志: tail ${APP_LOG}"
        exit 1
    fi
}

# ==================== stop 命令 ====================

cmd_stop() {
    divider
    echo -e "${CYAN}  $APP_NAME - 停止${NC}"
    divider

    pkill -f "watchdog.sh" 2>/dev/null && success "watchdog 已停止" || warn "watchdog 未在运行"
    pkill -f "python3 app.py" 2>/dev/null && success "app.py 已停止" || warn "app.py 未在运行"
    sleep 1
    echo ""
    success "已全部停止"
}

# ==================== restart 命令 ====================

cmd_restart() {
    cmd_stop
    echo ""
    cmd_start
}

# ==================== status 命令 ====================

cmd_status() {
    divider
    echo -e "${CYAN}  $APP_NAME - 运行状态${NC}"
    divider
    echo ""

    # 项目是否存在
    if [ ! -d "$PROJECT_DIR" ]; then
        error "项目未部署"
        exit 1
    fi

    # 读取配置
    local PORT="?"
    local API_KEY_SET="否"
    if [ -f "$CONFIG_FILE" ]; then
        PORT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['port'])" 2>/dev/null || echo "?")
        API_KEY_SET=$(python3 -c "
import json
c = json.load(open('$CONFIG_FILE'))
key = c.get('api_key', '')
print('是' if key and key != 'your apikey here' else '否')
" 2>/dev/null || echo "?")
    fi

    # watchdog 状态
    if is_watchdog_running; then
        echo -e "  watchdog:  ${GREEN}运行中${NC}"
    else
        echo -e "  watchdog:  ${RED}未运行${NC}"
    fi

    # app.py 状态
    if is_app_running; then
        local APP_PID=$(pgrep -f "python3 app.py" | head -1)
        echo -e "  app.py:    ${GREEN}运行中${NC} (PID: ${APP_PID})"
    else
        echo -e "  app.py:    ${RED}未运行${NC}"
    fi

    echo ""
    echo -e "  端口:      ${PORT}"
    echo -e "  API Key:   ${API_KEY_SET}"
    echo -e "  项目目录:  ${PROJECT_DIR}"
    echo -e "  应用日志:  ${APP_LOG}"
    echo -e "  守护日志:  ${WATCHDOG_LOG}"
    echo ""

    # Cloudflare 访问地址
    if is_app_running && [ "$PORT" != "?" ]; then
        echo -e "  直连访问:  ${CYAN}http://[你的VPS-IPv6地址]:${PORT}${NC}"
        echo -e "  CF 访问:   ${CYAN}https://你的域名${NC}（需配置 Cloudflare）"
    fi
    echo ""
}

# ==================== log 命令 ====================

cmd_log() {
    if [ ! -f "$APP_LOG" ]; then
        error "日志文件不存在: $APP_LOG"
        exit 1
    fi
    echo -e "${CYAN}实时日志（Ctrl+C 退出）：${NC}"
    tail -f "$APP_LOG"
}

# ==================== remove 命令 ====================

cmd_remove() {
    divider
    echo -e "${RED}  $APP_NAME - 彻底卸载${NC}"
    divider
    echo ""
    echo -e "${YELLOW}  即将执行以下操作：${NC}"
    echo "  ① 停止 watchdog 和 app.py 进程"
    echo "  ② 删除 ~/.profile 中的自启配置"
    echo "  ③ 删除项目目录: $PROJECT_DIR"
    echo ""
    echo -e "${RED}  ⚠️ 此操作不可恢复！${NC}"
    echo ""
    read -p "确认卸载？输入 YES 继续: " CONFIRM

    if [ "$CONFIRM" != "YES" ]; then
        info "已取消"
        exit 0
    fi

    echo ""

    # 1. 停止进程
    info "停止进程..."
    pkill -f "watchdog.sh" 2>/dev/null || true
    pkill -f "python3 app.py" 2>/dev/null || true
    sleep 1
    success "进程已停止"

    # 2. 删除自启配置
    info "删除自启配置..."
    sed -i '/mimo-clone/d' "$PROFILE_FILE" 2>/dev/null || true
    success "自启配置已删除"

    # 3. 删除项目目录
    info "删除项目文件..."
    if [ -d "$PROJECT_DIR" ]; then
        rm -rf "$PROJECT_DIR"
        success "项目目录已删除: $PROJECT_DIR"
    else
        warn "项目目录不存在，跳过"
    fi

    echo ""
    divider
    echo -e "${GREEN}  ✅ 卸载完成！${NC}"
    divider
    echo ""
    echo -e "  系统依赖（python3, git 等）未删除。"
    echo -e "  如需删除: ${CYAN}apk del python3 git${NC}"
    echo ""
}

# ==================== 帮助信息 ====================

cmd_help() {
    echo ""
    divider
    echo -e "${CYAN}  $APP_NAME - 管理脚本${NC}"
    divider
    echo ""
    echo "  用法: ./mimo.sh <命令>"
    echo ""
    echo "  命令列表:"
    echo -e "    ${GREEN}deploy${NC}    首次部署（检查环境、安装依赖、配置端口）"
    echo -e "    ${GREEN}start${NC}     启动应用 + 自动守护"
    echo -e "    ${GREEN}stop${NC}      停止应用 + 守护"
    echo -e "    ${GREEN}restart${NC}   重启应用"
    echo -e "    ${GREEN}status${NC}    查看运行状态"
    echo -e "    ${GREEN}log${NC}       查看实时日志"
    echo -e "    ${GREEN}remove${NC}    彻底卸载（停止服务、删除所有文件）"
    echo ""
    echo "  示例:"
    echo "    ./mimo.sh deploy     # 首次部署"
    echo "    ./mimo.sh start      # 启动"
    echo "    ./mimo.sh status     # 查看状态"
    echo ""
}

# ==================== 主入口 ====================

case "${1:-help}" in
    deploy)   cmd_deploy ;;
    start)    cmd_start ;;
    stop)     cmd_stop ;;
    restart)  cmd_restart ;;
    status)   cmd_status ;;
    log)      cmd_log ;;
    remove)   cmd_remove ;;
    help|*)   cmd_help ;;
esac
