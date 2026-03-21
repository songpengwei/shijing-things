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

cd "$SCRIPT_DIR"

# 1. 检查并激活 conda 环境
echo -e "${YELLOW}[1/5] 检查 conda 环境...${NC}"

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
echo -e "${YELLOW}[2/5] 安装依赖...${NC}"

if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    echo -e "  ${GREEN}✓ 依赖安装完成${NC}"
else
    echo -e "  ${RED}✗ 未找到 requirements.txt${NC}"
    exit 1
fi

# 3. 初始化数据库
echo ""
echo -e "${YELLOW}[3/5] 初始化数据库...${NC}"

# 检查是否需要重新初始化
if [ -f "shijing.db" ]; then
    echo "  数据库文件已存在"
    echo ""
    echo "  请选择操作:"
    echo "    1) 跳过数据库操作 (默认)"
    echo "    2) 从 shijing_things.json 重新加载数据"
    echo "    3) 完全重新初始化数据库 (删除并重建)"
    echo ""
    read -p "  请输入选项 (1/2/3): " -n 1 -r
    echo ""
    
    case $REPLY in
        2)
            echo "  正在从 shijing_things.json 重新加载数据..."
            python scripts/load_from_json.py
            ;;
        3)
            echo "  正在完全重新初始化数据库..."
            rm -f shijing.db
            echo "  已删除旧数据库"
            python scripts/init_db.py <<< "y"
            ;;
        *)
            echo "  跳过数据库操作"
            ;;
    esac
else
    python scripts/init_db.py <<< "y"
fi

# 4. 复制图片
echo ""
echo -e "${YELLOW}[4/5] 检查图片...${NC}"

img_source="data/img"
img_target="shijing_things/static/img"

if [ -d "$img_source" ]; then
    # 检查是否需要重新复制图片
    read -p "  是否重新复制图片到 $img_target? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  正在复制图片..."
        mkdir -p "$img_target"
        
        count=0
        for filename in "$img_source"/*; do
            if [ -f "$filename" ]; then
                basename=$(basename "$filename")
                cp "$filename" "$img_target/$basename"
                count=$((count + 1))
            fi
        done
        
        echo -e "  ${GREEN}✓ 复制了 $count 张图片${NC}"
    else
        echo "  跳过图片复制"
    fi
else
    echo -e "  ${YELLOW}⚠ 图片源目录不存在: $img_source${NC}"
fi

if [ ! -f "shijing.db" ]; then
    echo -e "  ${RED}✗ 数据库初始化失败${NC}"
    exit 1
fi

echo -e "  ${GREEN}✓ 数据库准备就绪${NC}"

# 5. 启动服务
echo ""
echo -e "${YELLOW}[5/5] 启动服务...${NC}"
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
uvicorn shijing_things.main:app --reload --host 0.0.0.0 --port 8000
