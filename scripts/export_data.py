#!/usr/bin/env python3
"""
数据库导出脚本
支持导出为 JSON 或 SQL 格式

用法:
    python scripts/export_data.py --format json --output data_export.json
    python scripts/export_data.py --format sql --output data_export.sql
    python scripts/export_data.py -f json -o data_export.json
"""
import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


# 项目根目录
ROOT_DIR = Path(__file__).parent.parent
DB_PATH = ROOT_DIR / "shijing.db"


def get_db_connection():
    """获取数据库连接"""
    if not DB_PATH.exists():
        print(f"错误: 数据库文件不存在: {DB_PATH}")
        sys.exit(1)
    
    return sqlite3.connect(DB_PATH)


def export_to_json(output_path: str):
    """导出为 JSON 格式"""
    print(f"正在导出为 JSON: {output_path}")
    
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 导出事物数据
    cursor.execute("SELECT * FROM shijing_items ORDER BY id")
    items = [dict(row) for row in cursor.fetchall()]
    
    # 导出诗篇数据
    cursor.execute("SELECT * FROM poems ORDER BY id")
    poems = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # 构建导出数据结构
    export_data = {
        "metadata": {
            "export_time": datetime.now().isoformat(),
            "version": "1.0.0",
            "source": "shijing-things",
            "description": "诗经事物数据库导出"
        },
        "stats": {
            "total_items": len(items),
            "total_poems": len(poems)
        },
        "items": items,
        "poems": poems
    }
    
    # 写入文件
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 导出完成: {output_file}")
    print(f"  - 事物数据: {len(items)} 条")
    print(f"  - 诗篇数据: {len(poems)} 条")
    
    return output_file


def export_to_sql(output_path: str):
    """导出为 SQL 格式"""
    print(f"正在导出为 SQL: {output_path}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    lines = [
        "-- 诗经事物数据库导出",
        f"-- 导出时间: {datetime.now().isoformat()}",
        "-- 来源: shijing-things",
        "",
        "PRAGMA foreign_keys=OFF;",
        "BEGIN TRANSACTION;",
        ""
    ]
    
    # 获取表结构
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name IN ('shijing_items', 'poems')")
    tables = cursor.fetchall()
    
    for table_name, create_sql in tables:
        lines.append(f"-- 表: {table_name}")
        lines.append(f"DROP TABLE IF EXISTS {table_name};")
        lines.append(f"{create_sql};")
        lines.append("")
        
        # 获取索引
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}' AND sql IS NOT NULL")
        indexes = cursor.fetchall()
        for (index_sql,) in indexes:
            lines.append(f"{index_sql};")
        lines.append("")
        
        # 获取数据
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        if rows:
            # 获取列名
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            lines.append(f"-- 插入 {table_name} 数据 ({len(rows)} 条)")
            
            for row in rows:
                values = []
                for value in row:
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        # 转义单引号
                        escaped = value.replace("'", "''")
                        values.append(f"'{escaped}'")
                    else:
                        values.append(str(value))
                
                sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
                lines.append(sql)
            
            lines.append("")
    
    lines.append("COMMIT;")
    lines.append("")
    
    conn.close()
    
    # 写入文件
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    # 统计信息
    cursor = get_db_connection().cursor()
    cursor.execute("SELECT COUNT(*) FROM shijing_items")
    items_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM poems")
    poems_count = cursor.fetchone()[0]
    cursor.connection.close()
    
    print(f"✓ 导出完成: {output_file}")
    print(f"  - 事物数据: {items_count} 条")
    print(f"  - 诗篇数据: {poems_count} 条")
    
    return output_file


def export_items_only(output_path: str):
    """仅导出事物数据为 JSON（兼容前端格式）"""
    print(f"正在导出事物数据: {output_path}")
    
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM shijing_items ORDER BY id")
    items = []
    
    for row in cursor.fetchall():
        item = dict(row)
        # 转换为驼峰命名（兼容旧前端格式）
        converted = {
            "id": item["id"],
            "name": item["name"],
            "category": item["category"],
            "title": item["title"],
            "chapter": item["chapter"],
            "section": item["section"],
            "poemId": item["poem_id"],
            "quote": item["quote"],
            "description": item["description"] or "",
            "imageUrl": item["image_url"] or "",
            "modernName": item["modern_name"] or "",
            "taxonomy": item["taxonomy"] or "",
            "symbolism": item["symbolism"] or "",
            "wikiLink": item["wiki_link"] or ""
        }
        items.append(converted)
    
    conn.close()
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 导出完成: {output_file}")
    print(f"  - 事物数据: {len(items)} 条")
    
    return output_file


def export_poems_only(output_path: str):
    """仅导出诗篇数据为 JSON（兼容前端格式）"""
    print(f"正在导出诗篇数据: {output_path}")
    
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM poems ORDER BY id")
    poems_dict = {}
    
    for row in cursor.fetchall():
        poem = dict(row)
        # 解析 content JSON 字符串
        try:
            content = json.loads(poem["content"])
        except:
            content = []
        
        poems_dict[poem["title"]] = {
            "title": poem["title"],
            "chapter": poem["chapter"],
            "section": poem["section"],
            "content": content,
            "fullSource": poem["full_source"]
        }
    
    conn.close()
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(poems_dict, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 导出完成: {output_file}")
    print(f"  - 诗篇数据: {len(poems_dict)} 条")
    
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="导出诗经事物数据库数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --format json --output export.json
  %(prog)s -f sql -o export.sql
  %(prog)s --format items -o items.json    # 仅导出事物数据
  %(prog)s --format poems -o poems.json    # 仅导出诗篇数据
        """
    )
    
    parser.add_argument(
        "-f", "--format",
        choices=["json", "sql", "items", "poems"],
        default="json",
        help="导出格式 (默认: json)"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="输出文件路径",
        default=None
    )
    
    args = parser.parse_args()
    
    # 设置默认输出文件名
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if args.format == "json":
            args.output = f"export_{timestamp}.json"
        elif args.format == "sql":
            args.output = f"export_{timestamp}.sql"
        elif args.format == "items":
            args.output = f"items_{timestamp}.json"
        elif args.format == "poems":
            args.output = f"poems_{timestamp}.json"
    
    # 执行导出
    print("=" * 60)
    print("诗经事物数据库导出")
    print("=" * 60)
    print(f"数据库: {DB_PATH}")
    print(f"格式: {args.format}")
    print(f"输出: {args.output}")
    print("")
    
    try:
        if args.format == "json":
            export_to_json(args.output)
        elif args.format == "sql":
            export_to_sql(args.output)
        elif args.format == "items":
            export_items_only(args.output)
        elif args.format == "poems":
            export_poems_only(args.output)
        
        print("")
        print("=" * 60)
        print("✓ 导出成功!")
        print("=" * 60)
        
    except Exception as e:
        print(f"")
        print("=" * 60)
        print(f"✗ 导出失败: {e}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
