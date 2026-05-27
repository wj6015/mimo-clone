#!/bin/sh

echo "=========================================="
echo " MiMo 声音克隆 Web 平台启动脚本"
echo "=========================================="

# 检查Python环境
PYTHON=""
PIP=""

if command -v python3 > /dev/null 2>&1; then
    PYTHON="python3"
    PIP="pip3"
elif command -v python > /dev/null 2>&1; then
    PYTHON="python"
    PIP="pip"
else
    echo "[ERR] 未找到Python，请先安装Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1)
echo "[OK] Python环境: $PYTHON_VERSION"

# 检查并安装依赖
echo "[INFO] 检查Python依赖..."

NEED_INSTALL=""

for dep in flask requests werkzeug; do
    if ! $PYTHON -c "import $dep" > /dev/null 2>&1; then
        NEED_INSTALL="$NEED_INSTALL $dep"
    fi
done

if [ -n "$NEED_INSTALL" ]; then
    echo "[INFO] 安装缺失依赖:$NEED_INSTALL"
    $PIP install $NEED_INSTALL
fi

# 可选依赖：pydub
if ! $PYTHON -c "import pydub" > /dev/null 2>&1; then
    echo "[INFO] pydub 未安装（可选），音频压缩功能将不可用"
    echo "[INFO] 如需安装: $PIP install pydub"
fi

echo "[OK] 依赖检查完成"

# 创建必要目录
mkdir -p static/css templates uploads outputs
echo "[OK] 目录结构已创建"

# 获取本机IP
LOCAL_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
[ -z "$LOCAL_IP" ] && LOCAL_IP="localhost"

echo ""
echo "=========================================="
echo "[WEB] 本机访问: http://localhost:8080"
echo "[WEB] 局域网访问: http://$LOCAL_IP:8080"
echo "=========================================="
echo "[NOTE] 首次运行请在网页顶部配置 API Key"
echo "[NOTE] 配置热加载，无需重启服务"
echo "=========================================="
echo "按 Ctrl+C 停止服务"
echo "=========================================="
echo ""

$PYTHON app.py
