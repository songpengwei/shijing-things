#!/usr/bin/env python3
"""
数据库初始化脚本
使用 SQL 文件初始化 SQLite 数据库
"""
import os
import sqlite3
import sys
from pathlib import Path


def init_database():
    """初始化数据库"""
    # 项目根目录
    root_dir = Path(__file__).parent.parent
    
    # 各目录路径
    db_path = root_dir / "shijing.db"
    sql_path = root_dir / "sql" / "init.sql"
    img_source = root_dir / "data" / "img"
    img_target = root_dir / "shijing_things" / "static" / "img"
    
    print("=" * 60)
    print("诗经事物数据库初始化")
    print("=" * 60)
    
    # 检查 SQL 文件是否存在
    if not sql_path.exists():
        print(f"错误: SQL 文件不存在: {sql_path}")
        sys.exit(1)
    
    # 如果数据库已存在，询问是否重建
    if db_path.exists():
        print(f"\n数据库已存在: {db_path}")
        response = input("是否重新初始化？(y/N): ").strip().lower()
        if response == 'y':
            os.remove(db_path)
            print("  已删除旧数据库")
        else:
            print("  取消初始化")
            return
    
    # 读取 SQL 文件
    print(f"\n[1/3] 读取 SQL 文件...")
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    print(f"  ✓ SQL 文件大小: {len(sql_content)} 字符")
    
    # 创建数据库并执行 SQL
    print(f"\n[2/3] 创建数据库...")
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(sql_content)
        conn.commit()
        
        # 验证数据
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM shijing_items")
        items_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM poems")
        poems_count = cursor.fetchone()[0]
        
        print(f"  ✓ 创建成功")
        print(f"  ✓ 事物数据: {items_count} 条")
        print(f"  ✓ 诗篇数据: {poems_count} 条")
    except Exception as e:
        print(f"  ✗ 错误: {e}")
        conn.close()
        sys.exit(1)
    finally:
        conn.close()
    
    # 复制图片
    print(f"\n[3/3] 复制图片...")
    if img_source.exists():
        os.makedirs(img_target, exist_ok=True)
        
        count = 0
        for filename in os.listdir(img_source):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                src = img_source / filename
                dst = img_target / filename
                import shutil
                shutil.copy2(src, dst)
                count += 1
        
        print(f"  ✓ 复制了 {count} 张图片")
    else:
        print(f"  ⚠ 图片源目录不存在: {img_source}")
    
    print("\n" + "=" * 60)
    print("数据库初始化完成!")
    print("=" * 60)
    print(f"数据库路径: {db_path}")
    print(f"启动命令: uvicorn shijing_things.main:app --reload")
    print("=" * 60)


if __name__ == "__main__":
    init_database()
