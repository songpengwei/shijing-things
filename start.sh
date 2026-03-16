#!/bin/bash
# 诗经事物 - 本地一键启动脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}      诗经事物 - 本地开发环境启动${NC}"
echo -e "${BLUE}==============================================${NC}"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"

cd "$SCRIPT_DIR"

# 1. 检查并激活 conda 环境
echo -e "${YELLOW}[1/4] 检查 conda 环境...${NC}"

# 检查是否在 conda 环境中
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    # 尝试激活环境
    if conda info --envs | grep -q "^shijing"; then
        echo "  找到 shijing 环境，正在激活..."
        # shellcheck source=/dev/null
        source "$(conda info --base)/etc/profile.d/conda.sh"
        conda activate shijing
        echo -e "  ${GREEN}✓ conda 环境已激活: $CONDA_DEFAULT_ENV${NC}"
    else
        echo -e "  ${RED}✗ 未找到 shijing 环境${NC}"
        echo ""
        echo "请使用以下命令创建环境:"
        echo "  conda create -n shijing python=3.11"
        echo ""
        exit 1
    fi
else
    echo -e "  ${GREEN}✓ 当前已在 conda 环境中: $CONDA_DEFAULT_ENV${NC}"
fi

# 2. 安装依赖
echo ""
echo -e "${YELLOW}[2/4] 安装依赖...${NC}"
cd "$BACKEND_DIR"

if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    echo -e "  ${GREEN}✓ 依赖安装完成${NC}"
else
    echo -e "  ${RED}✗ 未找到 requirements.txt${NC}"
    exit 1
fi

# 3. 初始化数据库
echo ""
echo -e "${YELLOW}[3/4] 初始化数据库...${NC}"

# 检查是否需要重新初始化
if [ -f "shijing.db" ]; then
    echo "  数据库文件已存在"
    read -p "  是否重新初始化数据库? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f shijing.db
        echo "  已删除旧数据库"
        python init_db.py <<< "y"
    else
        echo "  跳过数据库初始化"
    fi
else
    python init_db.py <<< "y"
fi

if [ ! -f "shijing.db" ]; then
    echo -e "  ${RED}✗ 数据库初始化失败${NC}"
    exit 1
fi

echo -e "  ${GREEN}✓ 数据库准备就绪${NC}"

# 4. 启动服务
echo ""
echo -e "${YELLOW}[4/4] 启动服务...${NC}"
echo ""
echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}  服务即将启动${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""
echo "  访问地址:"
echo "    - 首页:       http://localhost:8000"
echo "    - API 文档:   http://localhost:8000/api/docs"
echo "    - 管理页面:   http://localhost:8000/manage"
echo ""
echo "  快捷键:"
echo "    - Ctrl+C 停止服务"
echo ""
echo -e "${GREEN}==============================================${NC}"
echo ""

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
