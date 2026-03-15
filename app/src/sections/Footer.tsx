import { Heart, BookOpen } from 'lucide-react';
import { stats } from '@/data/shijingData';

export function Footer() {
  return (
    <footer className="bg-gradient-to-r from-amber-900 via-amber-800 to-amber-900 text-amber-100 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About */}
          <div>
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className="w-5 h-5" />
              <h3 className="font-bold text-lg">诗经草木鸟兽</h3>
            </div>
            <p className="text-amber-200 text-sm leading-relaxed">
              《诗经》是中国最早的诗歌总集，收录了西周初年至春秋中叶的诗歌305篇。
              孔子曰："多识于鸟兽草木之名"，本网站整理了《诗经》中涉及的草木鸟兽，
              共计{stats.total}种，以飨读者。
            </p>
          </div>

          {/* Stats */}
          <div>
            <h3 className="font-bold text-lg mb-4">数据统计</h3>
            <ul className="space-y-2 text-sm text-amber-200">
              <li className="flex justify-between">
                <span>草类植物</span>
                <span className="font-medium">{stats.grass} 种</span>
              </li>
              <li className="flex justify-between">
                <span>木类植物</span>
                <span className="font-medium">{stats.wood} 种</span>
              </li>
              <li className="flex justify-between">
                <span>鸟类动物</span>
                <span className="font-medium">{stats.bird} 种</span>
              </li>
              <li className="flex justify-between">
                <span>兽类动物</span>
                <span className="font-medium">{stats.beast} 种</span>
              </li>
              <li className="flex justify-between">
                <span>虫类动物</span>
                <span className="font-medium">{stats.insect} 种</span>
              </li>
              <li className="flex justify-between">
                <span>鱼类动物</span>
                <span className="font-medium">{stats.fish} 种</span>
              </li>
              <li className="flex justify-between border-t border-amber-700 pt-2 mt-2">
                <span className="font-bold text-amber-100">总计</span>
                <span className="font-bold text-amber-100">{stats.total} 种</span>
              </li>
            </ul>
          </div>

          {/* Quote */}
          <div>
            <h3 className="font-bold text-lg mb-4">经典名句</h3>
            <blockquote className="text-sm text-amber-200 italic leading-relaxed border-l-2 border-amber-500 pl-4 mb-4">
              "关关雎鸠，在河之洲。窈窕淑女，君子好逑。"
              <footer className="mt-2 text-amber-300 not-italic">
                ——《周南·关雎》
              </footer>
            </blockquote>
            <blockquote className="text-sm text-amber-200 italic leading-relaxed border-l-2 border-amber-500 pl-4">
              "蒹葭苍苍，白露为霜。所谓伊人，在水一方。"
              <footer className="mt-2 text-amber-300 not-italic">
                ——《秦风·蒹葭》
              </footer>
            </blockquote>
          </div>
        </div>

        {/* Copyright */}
        <div className="border-t border-amber-800 mt-8 pt-8 text-center text-sm text-amber-300">
          <p className="flex items-center justify-center gap-1">
            用 <Heart className="w-4 h-4 text-red-400 fill-red-400" /> 制作 | 传承中华文化
          </p>
        </div>
      </div>
    </footer>
  );
}
