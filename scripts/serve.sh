#!/bin/bash
# 启动诗经静态网站服务器

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$ROOT_DIR/app/dist"
echo "🌿 启动《诗经草木鸟兽大全》服务器..."
echo "📍 访问地址: http://localhost:8081"
echo "⚡ 按 Ctrl+C 停止服务器"
echo ""
python3 -m http.server 8081
