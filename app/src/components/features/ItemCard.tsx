import { useState, useEffect } from 'react';
import type { ShijingItem } from '@/types';
import poemFullText from '@/data/poemFullText.json';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Quote, BookOpen, Leaf, ScrollText, X, ExternalLink, Tag, TreePine } from 'lucide-react';

interface ItemCardProps {
  item: ShijingItem;
}

const categoryColors = {
  '草': 'from-green-50 to-emerald-50 border-green-200',
  '木': 'from-amber-50 to-yellow-50 border-amber-200',
  '鸟': 'from-blue-50 to-sky-50 border-blue-200',
  '兽': 'from-orange-50 to-red-50 border-orange-200',
  '虫': 'from-purple-50 to-violet-50 border-purple-200',
  '鱼': 'from-cyan-50 to-teal-50 border-cyan-200',
};

const categoryBadgeColors = {
  '草': 'bg-green-100 text-green-800',
  '木': 'bg-amber-100 text-amber-800',
  '鸟': 'bg-blue-100 text-blue-800',
  '兽': 'bg-orange-100 text-orange-800',
  '虫': 'bg-purple-100 text-purple-800',
  '鱼': 'bg-cyan-100 text-cyan-800',
};

export function ItemCard({ item }: ItemCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showFullText, setShowFullText] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);
  
  // 获取全文数据
  const fullPoem = poemFullText[item.poem as keyof typeof poemFullText];
  
  // 当弹窗关闭时重置全文显示状态
  useEffect(() => {
    if (!isOpen) {
      setShowFullText(false);
    }
  }, [isOpen]);

  return (
    <>
      <div
        onClick={() => setIsOpen(true)}
        className={`
          group relative overflow-hidden rounded-xl border-2 cursor-pointer
          bg-gradient-to-br ${categoryColors[item.category]}
          transition-all duration-300 hover:shadow-lg hover:scale-[1.02]
        `}
      >
        {/* Image Container */}
        <div className="relative h-48 overflow-hidden bg-gray-100">
          {!imageLoaded && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Leaf className="w-8 h-8 text-gray-300 animate-pulse" />
            </div>
          )}
          {item.imageUrl ? (
            <img
              src={item.imageUrl}
              alt={item.name}
              onLoad={() => setImageLoaded(true)}
              className={`
                w-full h-full object-cover transition-transform duration-500
                ${imageLoaded ? 'opacity-100' : 'opacity-0'}
                group-hover:scale-110
              `}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
              <span className="text-6xl">{item.category === '草' ? '🌱' : item.category === '木' ? '🌳' : item.category === '鸟' ? '🦅' : item.category === '兽' ? '🦌' : item.category === '虫' ? '🦋' : '🐟'}</span>
            </div>
          )}
          <div className="absolute top-3 left-3">
            <span className={`
              px-2 py-1 rounded-full text-xs font-medium
              ${categoryBadgeColors[item.category]}
            `}>
              {item.category}
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          <h3 className="text-xl font-bold text-gray-800 mb-1 group-hover:text-amber-700 transition-colors">
            {item.name}
          </h3>
          <div className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <BookOpen className="w-3 h-3" />
            <span>《{item.source}·{item.poem}》</span>
          </div>
          <p className="text-sm text-gray-600 line-clamp-2">
            {item.quote}
          </p>
        </div>
      </div>

      {/* Detail Dialog */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <span className="text-2xl">{item.name}</span>
              <span className={`
                px-3 py-1 rounded-full text-sm font-medium
                ${categoryBadgeColors[item.category]}
              `}>
                {item.category}类
              </span>
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* Image */}
            <div className="rounded-lg overflow-hidden border border-gray-200">
              {item.imageUrl ? (
                <img
                  src={item.imageUrl}
                  alt={item.name}
                  className="w-full h-64 object-cover"
                />
              ) : (
                <div className="w-full h-64 flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
                  <span className="text-8xl">{item.category === '草' ? '🌱' : item.category === '木' ? '🌳' : item.category === '鸟' ? '🦅' : item.category === '兽' ? '🦌' : item.category === '虫' ? '🦋' : '🐟'}</span>
                </div>
              )}
            </div>

            {/* Quote */}
            <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-lg">
              <div className="flex items-start gap-3">
                <Quote className="w-5 h-5 text-amber-500 flex-shrink-0 mt-1" />
                <div>
                  <p className="text-lg text-amber-900 font-medium italic leading-relaxed">
                    "{item.quote}"
                  </p>
                  <p className="text-sm text-amber-600 mt-2">
                    ——《{item.source}·{item.poem}》
                  </p>
                </div>
              </div>
            </div>

            {/* Detailed Info */}
            <div className="space-y-4">
              {/* 今名 */}
              <div className="flex items-start gap-3">
                <Tag className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                    今名
                  </h4>
                  <p className="text-gray-700">{item.modernName}</p>
                </div>
              </div>

              {/* 纲目属 */}
              <div className="flex items-start gap-3">
                <TreePine className="w-4 h-4 text-blue-500 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                    纲目属
                  </h4>
                  <p className="text-gray-700">{item.taxonomy}</p>
                </div>
              </div>

              {/* 寓意 */}
              <div className="bg-amber-50/50 rounded-lg p-4 border border-amber-100">
                <h4 className="text-sm font-semibold text-amber-700 uppercase tracking-wider mb-2">
                  寓意
                </h4>
                <p className="text-gray-700 leading-relaxed">
                  {item.symbolism}
                </p>
              </div>

              {/* 百科链接 */}
              {item.wikiLink && (
                <div className="flex items-center gap-2">
                  <ExternalLink className="w-4 h-4 text-blue-500" />
                  <a
                    href={item.wikiLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-700 hover:underline text-sm"
                  >
                    查看更多（维基百科/百度百科）
                  </a>
                </div>
              )}
            </div>

            {/* Original Description */}
            <div className="border-t border-gray-200 pt-4">
              <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">
                简注
              </h4>
              <p className="text-gray-600 text-sm leading-relaxed">
                {item.description}
              </p>
            </div>

            {/* Full Text Section */}
            {fullPoem && (
              <div className="border-t border-gray-200 pt-4">
                {!showFullText ? (
                  <button
                    onClick={() => setShowFullText(true)}
                    className="flex items-center gap-2 text-amber-600 hover:text-amber-700 font-medium transition-colors"
                  >
                    <ScrollText className="w-4 h-4" />
                    <span>查看《{item.poem}》全文</span>
                  </button>
                ) : (
                  <div className="bg-stone-50 rounded-lg p-4 border border-stone-200">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="text-sm font-semibold text-stone-500 uppercase tracking-wider flex items-center gap-2">
                        <ScrollText className="w-4 h-4" />
                        诗经全文
                      </h4>
                      <button
                        onClick={() => setShowFullText(false)}
                        className="text-stone-400 hover:text-stone-600 transition-colors"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="text-center mb-3">
                      <h5 className="text-lg font-bold text-stone-800">{fullPoem.title}</h5>
                      <p className="text-xs text-stone-500 mt-1">{fullPoem.fullSource}</p>
                    </div>
                    <div className="space-y-4">
                      {fullPoem.content.map((line: string, index: number) => (
                        <p key={index} className="text-stone-700 leading-loose text-left font-medium whitespace-pre-line">
                          {line}
                        </p>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
