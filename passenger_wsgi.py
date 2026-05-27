import sys
import os

# 获取当前目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 添加到 Python 路径
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入 Flask 应用
from app import app as application
