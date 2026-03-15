import { BookOpen } from 'lucide-react';
import { stats } from '@/data/shijingData';

export function Header() {
  return (
    <header className="bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 border-b border-amber-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col items-center text-center">
          <div className="flex items-center gap-3 mb-4">
            <BookOpen className="w-8 h-8 text-amber-700" />
            <span className="text-amber-600 text-sm tracking-widest uppercase">孔子曰：多识于鸟兽草木之名</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-amber-900 mb-4 tracking-tight">
            诗经草木鸟兽
          </h1>
          <p className="text-amber-700 max-w-2xl text-lg leading-relaxed mb-6">
            《诗经》三百篇，涉及草木鸟兽者过半。据统计，《诗经》中出现的植物约130余种，动物约100余种。
            古人以物起兴，借景抒情，这些草木鸟兽不仅是自然的写照，更是情感的寄托。
          </p>
          <div className="flex flex-wrap justify-center gap-3 text-sm">
            <span className="flex items-center gap-1 px-3 py-1 bg-white rounded-full shadow-sm">
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
              草类 {stats.grass}种
            </span>
            <span className="flex items-center gap-1 px-3 py-1 bg-white rounded-full shadow-sm">
              <span className="w-2 h-2 rounded-full bg-amber-600"></span>
              木类 {stats.wood}种
            </span>
            <span className="flex items-center gap-1 px-3 py-1 bg-white rounded-full shadow-sm">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              鸟类 {stats.bird}种
            </span>
            <span className="flex items-center gap-1 px-3 py-1 bg-white rounded-full shadow-sm">
              <span className="w-2 h-2 rounded-full bg-orange-500"></span>
              兽类 {stats.beast}种
            </span>
            <span className="flex items-center gap-1 px-3 py-1 bg-white rounded-full shadow-sm">
              <span className="w-2 h-2 rounded-full bg-purple-500"></span>
              虫类 {stats.insect}种
            </span>
            <span className="flex items-center gap-1 px-3 py-1 bg-white rounded-full shadow-sm">
              <span className="w-2 h-2 rounded-full bg-cyan-500"></span>
              鱼类 {stats.fish}种
            </span>
          </div>
          <div className="mt-4 text-amber-800 font-medium">
            共计 <span className="text-2xl text-amber-600">{stats.total}</span> 种
          </div>
        </div>
      </div>
    </header>
  );
}
