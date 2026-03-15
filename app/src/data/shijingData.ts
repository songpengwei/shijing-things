import shijingDataJson from './shijingData.json';

export interface ShijingItem {
  id: number;
  name: string;
  category: '草' | '木' | '鸟' | '兽' | '虫' | '鱼';
  poem: string;
  source: string;
  quote: string;
  description: string;
  imageUrl: string;
}

export const shijingData: ShijingItem[] = shijingDataJson as ShijingItem[];

export const categories = [
  { key: 'all', label: '全部', icon: '🌿' },
  { key: '草', label: '草类', icon: '🌱' },
  { key: '木', label: '木类', icon: '🌳' },
  { key: '鸟', label: '鸟类', icon: '🦅' },
  { key: '兽', label: '兽类', icon: '🦌' },
  { key: '虫', label: '虫类', icon: '🦋' },
  { key: '鱼', label: '鱼类', icon: '🐟' },
] as const;

export type CategoryKey = typeof categories[number]['key'];

// 统计
export const stats = {
  total: shijingData.length,
  grass: shijingData.filter(i => i.category === '草').length,
  wood: shijingData.filter(i => i.category === '木').length,
  bird: shijingData.filter(i => i.category === '鸟').length,
  beast: shijingData.filter(i => i.category === '兽').length,
  insect: shijingData.filter(i => i.category === '虫').length,
  fish: shijingData.filter(i => i.category === '鱼').length,
};
