# 诗经草木鸟兽大全

《诗经》三百篇，涉及草木鸟兽者过半。本网站整理了《诗经》中出现的草木鸟兽，共计100余种，以飨读者。

> 孔子曰："多识于鸟兽草木之名"

## 目录结构

```
shijing-things/
├── 📁 app/                    # React + Vite 前端项目
│   ├── 📁 src/
│   │   ├── 📁 components/     # 组件
│   │   │   ├── 📁 ui/         # shadcn/ui 基础组件
│   │   │   ├── 📁 layout/     # 布局组件（Header, Footer）
│   │   │   └── 📁 features/   # 业务功能组件（ItemCard）
│   │   ├── 📁 views/          # 页面视图（HomeView）
│   │   ├── 📁 hooks/          # 自定义 Hooks
│   │   ├── 📁 lib/            # 工具函数
│   │   ├── 📁 data/           # 前端静态数据
│   │   │   ├── shijingData.json      # 草木鸟兽数据
│   │   │   ├── poemFullText.json     # 诗经全文数据（由脚本生成）
│   │   │   └── shijingData.ts        # 数据导出 & 统计
│   │   ├── 📁 types/          # TypeScript 类型定义
│   │   ├── 📁 styles/         # 全局样式
│   │   ├── App.tsx            # 根组件
│   │   └── main.tsx           # 入口文件
│   ├── 📄 package.json        # 依赖配置
│   └── 📄 ...                 # 其他配置文件
│
├── 📁 data/                   # 原始数据文件
│   ├── shijing.json           # 诗经305篇全文（原始数据）
│   ├── shijing_data.json      # 草木鸟兽基础数据
│   └── image_mapping.json     # 图片映射数据
│
├── 📁 scripts/                # Python 脚本
│   ├── process_shijing.py     # 处理诗经数据生成 JSON
│   └── serve.sh               # 启动本地服务器
│
├── 📄 .gitignore              # Git 忽略配置
└── 📄 README.md               # 本文件
```

## 快速开始

### 安装依赖

```bash
cd app
npm install
```

### 开发模式

```bash
cd app
npm run dev
```

### 构建生产版本

```bash
cd app
npm run build
```

### 本地预览（使用脚本）

构建完成后，在项目根目录运行：

```bash
./scripts/serve.sh
```

然后访问 http://localhost:8080

## 数据更新

如需更新诗经全文数据：

```bash
cd scripts
python3 process_shijing.py
```

这会从 `data/shijing.json` 读取原始数据，处理后生成 `app/src/data/poemFullText.json`。

## 技术栈

- **框架**: React + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **UI 组件**: shadcn/ui
- **数据**: 诗经原始数据来自 [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) 开源项目

## 功能特性

- 🌿 按类别筛选：草、木、鸟、兽、虫、鱼
- 🔍 实时搜索：名称、诗篇、出处
- 📖 查看诗经全文：点击卡片查看完整诗篇
- 📱 响应式设计：支持移动端访问

## License

MIT
