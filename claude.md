# 诗经事物项目元信息

## 项目概述
- **项目名称**: shijing-things（诗经事物）
- **项目类型**: 前端 Web 应用
- **用途**: 展示《诗经》中提到的各种事物（草木鸟兽虫鱼）

## 技术栈
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **UI 组件库**: shadcn/ui
- **图标**: Lucide React

## 项目结构

```
shijing-things/
├── app/                        # 前端应用目录
│   ├── src/
│   │   ├── components/
│   │   │   ├── features/       # 功能组件
│   │   │   │   └── ItemCard.tsx    # 事物卡片组件（核心组件）
│   │   │   ├── layout/         # 布局组件
│   │   │   │   ├── Footer.tsx
│   │   │   │   └── Header.tsx
│   │   │   └── ui/             # shadcn/ui 组件库
│   │   │       ├── card.tsx, dialog.tsx, button.tsx 等
│   │   ├── data/               # 应用数据
│   │   │   ├── poemFullText.json   # 诗经全文数据（以诗名为 key）
│   │   │   ├── shijingData.json    # 事物列表数据
│   │   │   └── shijingData.ts      # 数据导出和类型
│   │   ├── hooks/              # 自定义 React Hooks
│   │   ├── lib/                # 工具函数
│   │   ├── styles/             # 样式文件
│   │   ├── types/              # TypeScript 类型定义
│   │   ├── views/              # 页面视图
│   │   │   └── HomeView.tsx
│   │   ├── App.tsx             # 主应用组件
│   │   └── main.tsx            # 应用入口
│   ├── dist/                   # 构建输出目录
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── data/                       # 原始数据目录
│   ├── shijing.json            # 诗经原文（按 ID 索引）
│   ├── shijing_data.json       # 事物数据（另一个版本）
│   ├── image_mapping.json      # 图片映射配置
│   └── img/                    # 事物图片资源
│       └── {id}_{name}.jpg/png/webp
├── scripts/                    # 脚本工具
├── README.md
└── .gitignore
```

## 数据文件格式

### 1. shijing.json（原始诗经数据）
```typescript
{
  "1": {
    "title": "关雎",
    "chapter": "国风",
    "section": "周南",
    "content": ["关关雎鸠...", "参差荇菜...", ...]  // 每章一行
  },
  ...
}
```

### 2. poemFullText.json（应用使用的全文数据）
```typescript
{
  "关雎": {
    "title": "关雎",
    "chapter": "国风",
    "section": "周南",
    "content": ["关关雎鸠...", "参差荇菜...", ...],
    "fullSource": "国风·周南·关雎"
  },
  ...
}
```

### 3. shijingData.json（事物列表）
```typescript
[
  {
    "id": 1,
    "name": "荇菜",
    "category": "草",        // 分类：草、木、鸟、兽、虫、鱼
    "source": "周南",
    "poem": "关雎",          // 所属诗篇
    "quote": "参差荇菜，左右流之",
    "description": "...",    // 简要注释
    "imageUrl": "...",       // 图片路径
    "modernName": "荇菜、莕菜、水荷叶",  // 今名（现代名称）
    "taxonomy": "龙胆科·荇菜属",         // 纲目属（分类学信息）
    "symbolism": "象征美好爱情与追求...", // 寓意（文化象征意义）
    "wikiLink": "https://zh.wikipedia.org/wiki/荇菜"  // 百科链接
  },
  ...
]
```

**数据规模**: 共 206 个事物
- 草类：62 个
- 木类：45 个
- 鸟类：36 个
- 兽类：27 个
- 虫类：21 个
- 鱼类：15 个

## 核心组件说明

### ItemCard.tsx
- **功能**: 展示单个事物的卡片
- **特性**:
  - 点击弹出详情 Dialog
  - 显示事物图片、名称、分类、引用诗句
  - **详情弹窗展示内容**:
    - 📛 **今名**: 现代名称（如：荇菜、莕菜、水荷叶）
    - 🌲 **纲目属**: 分类学信息（如：龙胆科·荇菜属）
    - 💡 **寓意**: 文化象征意义与诗意解读
    - 🔗 **百科链接**: 维基百科/百度百科外部链接
    - 📝 **简注**: 原简要注释
  - 可展开查看所属诗篇的完整内容
  - 支持按 JSON 中 content 数组多行渲染诗经全文
- **样式**: 使用渐变色边框区分不同分类

## 分类体系
事物按以下 6 类组织：
1. **草** - 草本植物
2. **木** - 树木植物
3. **鸟** - 鸟类
4. **兽** - 兽类
5. **虫** - 昆虫类
6. **鱼** - 鱼类

## 开发注意事项

### 修改诗经全文渲染
- 文件: `app/src/components/features/ItemCard.tsx`
- 渲染位置: Full Text Section 中的 `fullPoem.content.map`
- 当前实现: 使用 `whitespace-pre-line` 保留换行，每章之间用 `space-y-4` 分隔

### 添加新数据
1. 在 `shijingData.json` 中添加事物条目
2. 确保 `poemFullText.json` 中有对应诗篇的完整内容
3. 图片放入 `app/dist/img/` 或 `data/img/`

### 常用命令
```bash
cd app
npm run dev      # 开发服务器 (http://localhost:5173)
npm run build    # 构建
npm run preview  # 预览生产构建
```

### Node.js 版本兼容性
- **推荐版本**: Node.js 20.19+ 或 22.12+
- **当前环境**: Node.js 21.1.0（已降级 Vite 至 5.x 以兼容）
- **已降级包**: 
  - `vite`: 7.2.4 → 5.4.14
  - `@vitejs/plugin-react`: 5.1.1 → 4.3.4

## 文件路径速查
- **主数据**: `app/src/data/shijingData.json`
- **诗全文**: `app/src/data/poemFullText.json`
- **卡片组件**: `app/src/components/features/ItemCard.tsx`
- **首页视图**: `app/src/views/HomeView.tsx`
- **原始诗经**: `data/shijing.json`
- **类型定义**: `app/src/types/index.ts`
