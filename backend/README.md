# 诗经事物后端 API

基于 FastAPI + SQLAlchemy + SQLite 的诗经事物后端服务。

## 功能特性

- 🌿 完整的 CRUD 操作（事物、诗篇）
- 🔍 支持搜索和筛选
- 📊 统计数据 API
- 🖼️ 图片静态文件服务
- 📚 自动生成的 API 文档

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python init_db.py
```

这将：
- 创建 SQLite 数据库
- 导入事物数据（206 条）
- 导入诗篇数据
- 复制图片文件

### 3. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. 访问 API 文档

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API 端点

### 事物 (Items)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/items/` | 获取事物列表 |
| GET | `/api/items/{id}` | 获取单个事物 |
| POST | `/api/items/` | 创建事物 |
| PUT | `/api/items/{id}` | 更新事物 |
| DELETE | `/api/items/{id}` | 删除事物 |
| GET | `/api/items/stats` | 获取统计信息 |
| GET | `/api/items/categories` | 获取所有分类 |

### 诗篇 (Poems)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/poems/` | 获取诗篇列表 |
| GET | `/api/poems/{id}` | 获取诗篇 |
| GET | `/api/poems/title/{title}` | 根据标题获取诗篇 |
| POST | `/api/poems/` | 创建诗篇 |
| PUT | `/api/poems/{id}` | 更新诗篇 |
| DELETE | `/api/poems/{id}` | 删除诗篇 |

## 查询参数

### 列表查询

- `skip`: 跳过记录数（默认 0）
- `limit`: 返回记录数（默认 100，最大 1000）
- `category`: 按分类筛选（草、木、鸟、兽、虫、鱼）
- `search`: 搜索关键词（名称、诗篇、出处、引用）

### 示例

```bash
# 获取所有草类事物
curl "http://localhost:8000/api/items/?category=草"

# 搜索包含"雎鸠"的事物
curl "http://localhost:8000/api/items/?search=雎鸠"

# 分页获取
curl "http://localhost:8000/api/items/?skip=10&limit=20"
```

## Docker 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 仅启动后端
docker-compose up -d backend

# 查看日志
docker-compose logs -f backend
```

## 数据结构

### 事物 (ShijingItem)

```json
{
  "id": 1,
  "name": "荇菜",
  "category": "草",
  "poem": "关雎",
  "source": "周南",
  "quote": "参差荇菜，左右流之。",
  "description": "水生睡菜，嫩叶可食",
  "image_url": "/img/1_荇菜.jpg",
  "modern_name": "荇菜、莕菜、水荷叶",
  "taxonomy": "龙胆科·荇菜属",
  "symbolism": "象征美好爱情与追求...",
  "wiki_link": "https://zh.wikipedia.org/wiki/荇菜"
}
```

### 诗篇 (Poem)

```json
{
  "id": 1,
  "title": "关雎",
  "chapter": "国风",
  "section": "周南",
  "content": "[\"关关雎鸠...\", \"参差荇菜...\"]",
  "full_source": "国风·周南·关雎"
}
```
