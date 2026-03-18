#!/usr/bin/env python3
"""
验证 shijing_things.json 中的 quote 是否能在对应 poem_id 的 content 中找到
"""
import json
from pathlib import Path


def load_json(path: Path) -> dict | list:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_quotes():
    root_dir = Path(__file__).parent.parent
    data_dir = root_dir / 'data'
    
    things = load_json(data_dir / 'shijing_things.json')
    poems = load_json(data_dir / 'shijing.json')
    
    errors = []
    warnings = []
    
    print("=" * 60)
    print("验证 quote 匹配")
    print("=" * 60)
    
    for item in things:
        item_id = item['id']
        name = item['name']
        quote = item['quote']
        poem_id = str(item['poem_id'])
        
        # 检查 poem_id 是否存在
        if poem_id not in poems:
            errors.append({
                'id': item_id,
                'name': name,
                'poem_id': poem_id,
                'quote': quote,
                'error': f'poem_id {poem_id} 不存在'
            })
            continue
        
        poem = poems[poem_id]
        content = poem['content']
        
        # 检查 quote 是否在 content 中
        found = False
        for line in content:
            if quote.strip('。，！？、；：""''（）【】') in line or line in quote:
                found = True
                break
            # 模糊匹配：取 quote 前5个字
            if len(quote) >= 5:
                if quote[:5] in line:
                    found = True
                    break
        
        if not found:
            errors.append({
                'id': item_id,
                'name': name,
                'poem_id': poem_id,
                'title': poem['title'],
                'chapter': poem['chapter'],
                'section': poem['section'],
                'quote': quote,
                'content_preview': content[0][:50] if content else '空',
                'error': f'quote 不在 poem_id={poem_id} 的 content 中'
            })
    
    # 输出结果
    if errors:
        print(f"\n❌ 发现 {len(errors)} 处错误:\n")
        for e in errors:
            print(f"  ID={e['id']}, 名称={e['name']}")
            print(f"    poem_id: {e.get('poem_id', 'N/A')}")
            if 'title' in e:
                print(f"    诗篇: {e['chapter']}·{e['section']}·{e['title']}")
            print(f"    quote: {e['quote']}")
            if 'content_preview' in e:
                print(f"    content: {e['content_preview']}...")
            print(f"    错误: {e['error']}")
            print()
    else:
        print("\n✅ 所有 quote 验证通过!")
    
    print("=" * 60)
    
    return len(errors)


if __name__ == '__main__':
    exit_code = verify_quotes()
    exit(1 if exit_code > 0 else 0)
