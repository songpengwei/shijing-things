#!/usr/bin/env python3
"""
从 shijing_things.json 加载数据到 SQLite 数据库
"""
import json
import sqlite3
import sys
from pathlib import Path


def load_from_json():
    """从 JSON 文件加载数据到数据库"""
    root_dir = Path(__file__).parent.parent
    
    db_path = root_dir / "shijing.db"
    json_path = root_dir / "data" / "shijing_things.json"
    poems_json_path = root_dir / "data" / "shijing.json"
    
    print("=" * 60)
    print("从 shijing_things.json 重新加载数据")
    print("=" * 60)
    
    # 检查文件是否存在
    if not json_path.exists():
        print(f"错误: JSON 文件不存在: {json_path}")
        sys.exit(1)
    
    if not db_path.exists():
        print(f"错误: 数据库不存在: {db_path}")
        print("请先运行 init_db.py 初始化数据库")
        sys.exit(1)
    
    # 读取 JSON 文件
    print(f"\n[1/3] 读取 shijing_things.json...")
    with open(json_path, 'r', encoding='utf-8') as f:
        items = json.load(f)
    print(f"  ✓ 读取了 {len(items)} 条事物数据")
    
    # 读取诗篇 JSON
    poems = []
    if poems_json_path.exists():
        print(f"\n[2/3] 读取 shijing.json...")
        with open(poems_json_path, 'r', encoding='utf-8') as f:
            poems = json.load(f)
        print(f"  ✓ 读取了 {len(poems)} 条诗篇数据")
    else:
        print(f"\n[2/3] 跳过诗篇数据 (文件不存在)")
    
    # 连接到数据库
    print(f"\n[3/3] 更新数据库...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 清空旧数据
        cursor.execute("DELETE FROM shijing_items")
        cursor.execute("DELETE FROM poems")
        
        # 插入事物数据
        for item in items:
            cursor.execute("""
                INSERT INTO shijing_items 
                (id, name, category, title, chapter, section, poem_id, quote, description, image_url,
                 modern_name, taxonomy, symbolism, wiki_link)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.get('id'),
                item.get('name', ''),
                item.get('category', ''),
                item.get('title', ''),
                item.get('chapter', ''),
                item.get('section', ''),
                item.get('poem_id', 0),
                item.get('quote', ''),
                item.get('description', ''),
                item.get('image_url', ''),
                item.get('modern_name', ''),
                item.get('taxonomy', ''),
                item.get('symbolism', ''),
                item.get('wiki_link', '')
            ))
        
        # 插入诗篇数据 (shijing.json 是字典格式，键是id)
        if isinstance(poems, dict):
            for poem_id, poem in poems.items():
                cursor.execute("""
                    INSERT INTO poems 
                    (id, title, chapter, section, content, full_source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    int(poem_id),
                    poem.get('title', ''),
                    poem.get('chapter', ''),
                    poem.get('section', ''),
                    json.dumps(poem.get('content', []), ensure_ascii=False),
                    poem.get('full_source', '')
                ))
        else:
            # 兼容列表格式
            for poem in poems:
                cursor.execute("""
                    INSERT INTO poems 
                    (id, title, chapter, section, content, full_source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    poem.get('id'),
                    poem.get('title', ''),
                    poem.get('chapter', ''),
                    poem.get('section', ''),
                    json.dumps(poem.get('content', []), ensure_ascii=False),
                    poem.get('full_source', '')
                ))
        
        conn.commit()
        
        # 验证数据
        cursor.execute("SELECT COUNT(*) FROM shijing_items")
        items_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM poems")
        poems_count = cursor.fetchone()[0]
        
        print(f"  ✓ 更新成功")
        print(f"  ✓ 事物数据: {items_count} 条")
        print(f"  ✓ 诗篇数据: {poems_count} 条")
        
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()
    
    print("\n" + "=" * 60)
    print("数据加载完成!")
    print("=" * 60)


if __name__ == "__main__":
    load_from_json()
