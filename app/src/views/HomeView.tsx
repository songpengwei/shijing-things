import { useState, useMemo } from 'react';
import { shijingData, categories } from '@/data/shijingData';
import type { CategoryKey } from '@/types';
import { ItemCard } from '@/components/features/ItemCard';
import { Search } from 'lucide-react';
import { Input } from '@/components/ui/input';

export function HomeView() {
  const [activeCategory, setActiveCategory] = useState<CategoryKey>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredItems = useMemo(() => {
    return shijingData.filter(item => {
      const matchesCategory = activeCategory === 'all' || item.category === activeCategory;
      const matchesSearch = 
        item.name.includes(searchQuery) ||
        item.poem.includes(searchQuery) ||
        item.source.includes(searchQuery) ||
        item.quote.includes(searchQuery);
      return matchesCategory && matchesSearch;
    });
  }, [activeCategory, searchQuery]);

  return (
    <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Filter and Search */}
      <div className="mb-8 space-y-4">
        {/* Category Filter */}
        <div className="flex flex-wrap gap-2 justify-center">
          {categories.map((cat) => (
            <button
              key={cat.key}
              onClick={() => setActiveCategory(cat.key)}
              className={`
                px-4 py-2 rounded-full text-sm font-medium transition-all duration-200
                flex items-center gap-2
                ${activeCategory === cat.key
                  ? 'bg-amber-600 text-white shadow-md'
                  : 'bg-white text-gray-600 border border-gray-200 hover:border-amber-300 hover:bg-amber-50'
                }
              `}
            >
              <span>{cat.icon}</span>
              <span>{cat.label}</span>
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="relative max-w-md mx-auto">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            type="text"
            placeholder="搜索草木鸟兽、诗篇或出处..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 border-gray-200 focus:border-amber-400 focus:ring-amber-400"
          />
        </div>
      </div>

      {/* Results Count */}
      <div className="mb-6 text-center text-sm text-gray-500">
        共找到 <span className="font-medium text-amber-600">{filteredItems.length}</span> 种草木鸟兽
      </div>

      {/* Grid */}
      {filteredItems.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredItems.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <div className="text-6xl mb-4">🌿</div>
          <h3 className="text-lg font-medium text-gray-600 mb-2">未找到相关内容</h3>
          <p className="text-gray-400">请尝试其他搜索词或筛选条件</p>
        </div>
      )}
    </main>
  );
}
