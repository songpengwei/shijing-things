# 诗经事物项目 - 开发指南

## 项目概述

**诗经草木鸟兽大全** - 《诗经》三百篇，涉及草木鸟兽者过半。本项目整理了《诗经》中出现的 204 种草木鸟兽，提供完整的增删改查功能。

> 孔子曰："多识于鸟兽草木之名"

## 技术栈

- **后端**: FastAPI + SQLAlchemy + SQLite
- **前端**: Jinja2 模板 + 纯 HTML/CSS/JavaScript
- **Python**: 3.11+
- **部署**: Docker / Docker Compose

## 项目结构

```
shijing-things/
├── shijing_things/            # Python 包（主应用）
│   ├── main.py                # FastAPI 入口
│   ├── core/                  # 配置 & 数据库
│   ├── models/                # SQLAlchemy 模型
│   ├── schemas/               # Pydantic 模型
│   ├── crud/                  # 数据库操作
│   ├── routers/               # 路由
│   │   ├── pages.py           # HTML 页面路由
│   │   └── api.py             # REST API 路由
│   ├── templates/             # Jinja2 模板
│   └── static/                # CSS/JS/图片
├── data/                      # 原始数据
│   ├── img/                   # 191张图片
│   ├── shijing.json           # 诗经原文
│   └── shijing_data.json      # 事物数据
├── sql/
│   └── init.sql               # 数据库初始化 SQL
├── scripts/
│   └── init_db.py             # 初始化脚本
├── tests/                     # 测试目录
├── docker-compose.yml         # Docker 配置
├── Dockerfile                 # 镜像构建
├── requirements.txt           # Python 依赖
├── start.sh                   # macOS/Linux 启动脚本
├── start.ps1                  # Windows 启动脚本
└── README.md                  # 项目文档
```

## 环境要求

- Python 3.11+
- Conda (推荐) 或 venv
- SQLite (内置)
- Docker (可选)

## 快速启动

### 方式一：一键启动（推荐）

**macOS/Linux:**
```bash
# 首次：创建 conda 环境
conda create -n shijing python=3.11 -y

# 一键启动（自动激活环境、安装依赖、初始化数据库、启动服务）
./start.sh
```

**Windows:**
```powershell
# 首次：创建 conda 环境
conda create -n shijing python=3.11 -y

# 一键启动
.\start.ps1
```

### 方式二：手动启动

```bash
# 1. 激活环境
conda activate shijing

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库（首次）
python scripts/init_db.py

# 4. 启动服务
uvicorn shijing_things.main:app --reload --host 0.0.0.0 --port 8000
```

### 方式三：Docker 启动

```bash
# 构建并启动
docker-compose up -d

# 初始化数据库（首次）
docker-compose exec app python scripts/init_db.py
```

## 访问地址

启动后访问：
- **首页**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/docs
- **管理页面**: http://localhost:8000/manage
- **健康检查**: http://localhost:8000/api/health

## 数据库

- **类型**: SQLite
- **文件**: `shijing.db` (项目根目录)
- **初始化**: `sql/init.sql` (包含 204 条事物 + 295 条诗篇)
- **图片**: `shijing_things/static/img/` (192 张)

### 重新初始化数据库

```bash
# 删除旧数据库
rm shijing.db

# 重新初始化
python scripts/init_db.py
```

## 主要依赖

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlalchemy==2.0.36
pydantic==2.9.2
pydantic-settings==2.6.1
jinja2==3.1.4
python-multipart==0.0.17
aiofiles==24.1.0
```

## 常用命令

```bash
# 启动开发服务器
uvicorn shijing_things.main:app --reload

# 生产模式启动
uvicorn shijing_things.main:app --host 0.0.0.0 --port 8000

# 运行测试
pytest tests/

# Docker 构建
docker-compose build

# Docker 停止
docker-compose down

# 查看日志
docker-compose logs -f

# 导出数据库为 JSON
python scripts/export_data.py -f json -o export.json

# 导出数据库为 SQL
python scripts/export_data.py -f sql -o export.sql

# 导出事物数据（兼容前端格式）
python scripts/export_data.py -f items -o items.json

# 导出诗篇数据（兼容前端格式）
python scripts/export_data.py -f poems -o poems.json
```

## 配置说明

配置文件：`shijing_things/core/config.py`

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `app_name` | 诗经事物 API | 应用名称 |
| `app_version` | 1.0.0 | 版本号 |
| `database_url` | sqlite:///./shijing.db | 数据库路径 |
| `static_dir` | ./shijing_things/static | 静态文件目录 |
| `img_dir` | ./shijing_things/static/img | 图片目录 |

## API 端点

### 事物 (Items)
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/items/` | 列表（支持筛选、搜索） |
| GET | `/api/items/{id}` | 详情 |
| POST | `/api/items/` | 创建 |
| PUT | `/api/items/{id}` | 更新 |
| DELETE | `/api/items/{id}` | 删除 |
| GET | `/api/items/stats` | 统计数据 |
| GET | `/api/items/categories` | 分类列表 |

### 诗篇 (Poems)
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/poems/` | 列表 |
| GET | `/api/poems/{id}` | 详情 |
| GET | `/api/poems/title/{title}` | 按标题查询 |
| POST | `/api/poems/` | 创建 |
| PUT | `/api/poems/{id}` | 更新 |
| DELETE | `/api/poems/{id}` | 删除 |

## 页面路由

| 路径 | 描述 |
|------|------|
| `/` | 首页 - 事物卡片列表 |
| `/item/{id}` | 事物详情页 |
| `/manage` | 数据管理页（表格） |
| `/manage/item/new` | 新建事物 |
| `/manage/item/{id}` | 编辑事物 |

## 数据规模

- **事物**: 204 条
  - 草类: 62 个
  - 木类: 44 个
  - 鸟类: 35 个
  - 兽类: 27 个
  - 虫类: 21 个
  - 鱼类: 15 个
- **诗篇**: 295 条
- **图片**: 192 张

## 开发注意事项

### 添加新字段

1. 修改模型：`shijing_things/models/models.py`
2. 修改 Schema：`shijing_things/schemas/schemas.py`
3. 更新 SQL：`sql/init.sql`
4. 更新模板：`shijing_things/templates/edit.html`
5. 重新初始化数据库

### 导入路径

所有导入使用 `shijing_things` 作为根包名：

```python
from shijing_things.core.config import get_settings
from shijing_things.crud.crud import item
from shijing_things.models.models import ShijingItem
```

### 图片路径

- 数据库存储：`/static/img/xxx.jpg`
- 实际位置：`shijing_things/static/img/xxx.jpg`

## 故障排查

### 数据库找不到
```bash
# 检查文件是否存在
ls -la shijing.db

# 重新初始化
python scripts/init_db.py
```

### 图片 404
```bash
# 检查图片是否存在
ls shijing_things/static/img/

# 检查路径是否正确（应为 /static/img/xxx.jpg）
```

## 数据导出

使用 `scripts/export_data.py` 脚本导出数据库数据：

### 导出格式

| 格式 | 说明 | 用途 |
|------|------|------|
| `json` | 完整数据库 JSON | 数据备份、迁移 |
| `sql` | SQL 插入语句 | 数据库重建、迁移 |
| `items` | 事物数据（驼峰命名） | 兼容前端格式 |
| `poems` | 诗篇数据（按标题索引） | 兼容前端格式 |

### 导出示例

```bash
# 导出为 JSON（默认）
python scripts/export_data.py

# 导出为 JSON（指定文件名）
python scripts/export_data.py -f json -o backup.json

# 导出为 SQL
python scripts/export_data.py -f sql -o backup.sql

# 导出事物数据（前端兼容格式）
python scripts/export_data.py -f items -o shijingData.json

# 导出诗篇数据（前端兼容格式）
python scripts/export_data.py -f poems -o poemFullText.json
```

### 导出 JSON 结构

```json
{
  "metadata": {
    "export_time": "2024-03-16T20:00:00",
    "version": "1.0.0",
    "source": "shijing-things"
  },
  "stats": {
    "total_items": 204,
    "total_poems": 295
  },
  "items": [...],
  "poems": [...]
}
```

### 导入错误
```bash
# 确保在项目根目录运行
pwd  # 应显示 .../shijing-things

# 检查 Python 路径
python -c "import sys; print(sys.path)"
```

### 端口占用
```bash
# 更换端口启动
uvicorn shijing_things.main:app --reload --port 8080
```

## 快捷键

- `Ctrl+C` - 停止服务
- `Ctrl+S` - 保存文件（触发 reload）

## 部署建议

### 生产环境

1. 使用 Gunicorn + Uvicorn
2. 配置反向代理（Nginx）
3. 设置环境变量
4. 定期备份数据库

### Docker 生产部署

```bash
# 构建镜像
docker-compose build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

---

**最后更新**: 2024-03-16
