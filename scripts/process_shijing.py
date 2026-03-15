#!/usr/bin/env python3
"""
处理诗经数据，创建以篇名为 key 的索引
"""
import json
import os

def process_shijing():
    # 获取项目根目录（脚本在 scripts/ 目录下）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    
    # 读取原始数据
    input_path = os.path.join(root_dir, 'data', 'shijing.json')
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 创建以篇名为 key 的字典
    poem_dict = {}
    
    for key, value in data.items():
        title = value['title']
        chapter = value['chapter']  # 国风/小雅/大雅/周颂/鲁颂/商颂
        section = value['section']  # 周南/召南/邶风 等
        content = value['content']  # 诗歌内容数组
        
        poem_dict[title] = {
            'title': title,
            'chapter': chapter,
            'section': section,
            'content': content,
            'fullSource': f"{chapter}·{section}·{title}" if section != title else f"{chapter}·{title}"
        }
    
    # 保存处理后的数据到前端目录
    output_path = os.path.join(root_dir, 'app', 'src', 'data', 'poemFullText.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(poem_dict, f, ensure_ascii=False, indent=2)
    
    print(f"处理完成！共 {len(poem_dict)} 篇")
    print(f"输出文件: {output_path}")
    
    # 打印一些示例
    print("\n前5篇示例:")
    for i, (title, info) in enumerate(list(poem_dict.items())[:5]):
        print(f"  {title}: {info['fullSource']}")
    
    return poem_dict

if __name__ == '__main__':
    process_shijing()
