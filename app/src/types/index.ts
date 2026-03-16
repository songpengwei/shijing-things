/**
 * 诗经数据类型定义
 */

// 分类类型
export type CategoryType = '草' | '木' | '鸟' | '兽' | '虫' | '鱼';

// 诗经条目接口
export interface ShijingItem {
  id: number;
  name: string;
  category: CategoryType;
  poem: string;
  source: string;
  quote: string;
  description: string;
  imageUrl: string;
  // 详细释义
  modernName: string;   // 今名
  taxonomy: string;     // 纲目属
  symbolism: string;    // 寓意
  wikiLink: string;     // 百科链接
}

// 分类配置
export interface CategoryConfig {
  key: 'all' | CategoryType;
  label: string;
  icon: string;
}

// 分类 Key 类型
export type CategoryKey = 'all' | CategoryType;

// 诗经全文数据结构
export interface PoemFullText {
  title: string;
  chapter: string;
  section: string;
  content: string[];
  fullSource: string;
}
