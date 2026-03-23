# 诗经草木鸟兽大全

《诗经》三百篇，涉及草木鸟兽者过半。本项目整理了《诗经》中出现的 204 种草木鸟兽，以飨读者。

> 孔子曰："多识于鸟兽草木之名"

## 技术架构

**后端**: FastAPI + SQLAlchemy + SQLite  
**前端**: 纯 HTML + CSS + JavaScript (Jinja2 模板)  
**部署**: Docker + Docker Compose

## 目录结构

```
shijing-things/
├── shijing_things/            # Python 包
│   ├── __init__.py
│   ├── main.py                # FastAPI 主应用
│   ├── core/                  # 配置和数据库
│   ├── models/                # SQLAlchemy 模型
│   ├── schemas/               # Pydantic 模型
│   ├── crud/                  # 数据库操作
│   ├── routers/               # 路由
│   │   ├── pages.py           # 页面路由 (HTML)
│   │   └── api.py             # API 路由 (JSON)
│   ├── templates/             # Jinja2 模板
│   └── static/                # 静态文件
│       ├── css/style.css
│       ├── js/app.js
│       └── img/               # 图片资源
├── data/                      # 原始数据
│   ├── shijing.json           # 诗经原文
│   ├── shijing_things.json    # 事物基础数据
│   └── img/                   # 原始图片
├── sql/
│   └── init.sql               # 数据库初始化 SQL
├── scripts/
│   └── init_db.py             # 数据库初始化脚本
├── tests/                     # 测试目录
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── start.sh                   # macOS/Linux 一键启动
├── start.ps1                  # Windows 一键启动
└── README.md
```

## 快速开始

## 环境变量

项目配置从项目根目录 `.env` 读取，不需要再去改 `shijing_things/core/config.py`。

```bash
cp .env.example .env
```

至少需要按部署域名填写这些值：

```env
admin_username=replace-with-admin-username
admin_password=replace-with-admin-password

github_client_id=your_github_client_id
github_client_secret=your_github_client_secret
github_redirect_uri=https://shi.qtmuniao.com/auth/github/callback

wechat_app_id=your_wechat_app_id
wechat_app_secret=your_wechat_app_secret
wechat_redirect_uri=https://shi.qtmuniao.com/auth/wechat/callback
```

说明：
- `.env` 已被 `.gitignore` 忽略，不要提交真实密钥。
- 管理员账号从 `.env` 读取，但不要把真实密码写进仓库或模板。
- `github_redirect_uri` 和 `wechat_redirect_uri` 必须写完整回调路径，不能只写域名。
- 如果你刚刚泄露过 `github_client_secret`，应先去 GitHub 重新生成新的 secret。

### 方式一: 一键启动（推荐）

**macOS/Linux:**
```bash
# 确保已创建 conda 环境
conda create -n shijing python=3.11 -y

# 一键启动
./start.sh
```

**Windows:**
```powershell
# 确保已创建 conda 环境
conda create -n shijing python=3.11 -y

# 一键启动
.\start.ps1
```

脚本会自动：
1. 激活 conda 环境 `shijing`
2. 安装 Python 依赖
3. 初始化数据库（首次运行）
4. 启动开发服务器

### 方式二: Docker 部署

```bash
# 1. 构建并启动
docker-compose up -d

# 2. 初始化数据库（首次运行）
docker-compose exec app python init_db.py

# 3. 访问
# 网站: http://localhost:8000
# API 文档: http://localhost:8000/api/docs
```

### 方式三: 手动运行

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 初始化数据库
python init_db.py

# 4. 启动服务
uvicorn shijing_things.main:app --reload --host 0.0.0.0 --port 8000

# 5. 访问 http://localhost:8000
```

## 数据初始化

数据库使用 SQL 文件初始化 (`backend/init.sql`)，包含：
- 事物数据：204 条
- 诗篇数据：295 条
- 图片资源：191 张

```bash
# 重新初始化数据库
cd backend
python init_db.py
```

## 功能特性

### 1. 前端页面
- **首页** (`/`): 展示事物卡片，支持分类筛选和搜索
- **详情页** (`/item/{id}`): 展示事物详细信息，包括诗经全文
- **管理页** (`/manage`): 数据管理，表格形式展示所有数据
- **编辑页** (`/manage/item/{id}` 或 `/manage/item/new`): 新增/编辑事物

### 2. RESTful API
- 完整的 CRUD 操作
- 自动生成的 API 文档 (/api/docs)
- 支持分类筛选、搜索、分页

### 3. 数据库模型

**事物 (ShijingItem)**:
- id, name, category, poem, source, quote
- description, image_url
- modern_name, taxonomy, symbolism, wiki_link

**诗篇 (Poem)**:
- id, title, chapter, section, content, full_source

## API 端点

### 事物 (Items)
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/items/` | 列表（支持筛选、搜索） |
| GET | `/api/items/{id}` | 详情 |
| POST | `/api/items/` | 创建 |
| PUT | `/api/items/{id}` | 更新 |
| DELETE | `/api/items/{id}` | 删除 |
| GET | `/api/items/stats` | 统计 |
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

## 数据规模

共 **204** 个事物：
- 草类：62 个
- 木类：44 个
- 鸟类：35 个
- 兽类：27 个
- 虫类：21 个
- 鱼类：15 个

## 开发说明

### 添加新字段

1. **修改模型** (`app/models/models.py`)
2. **修改 Schema** (`app/schemas/schemas.py`)
3. **修改 SQL 文件** (`init.sql`)
4. **修改表单** (`app/templates/edit.html`)
5. **修改列表/详情页** (`app/templates/index.html`, `detail.html`)

### 样式调整

所有样式在 `backend/static/css/style.css` 中，使用 CSS 变量方便主题定制。

## License

MIT
