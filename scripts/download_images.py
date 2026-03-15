#!/usr/bin/env python3
"""
下载所有图片到本地，并更新数据文件使用本地图片路径
"""
import json
import os
import urllib.request
import urllib.error
from urllib.parse import urlparse
import hashlib

# 获取项目根目录
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)

def get_file_extension(url):
    """从 URL 获取文件扩展名"""
    parsed = urlparse(url)
    path = parsed.path
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
        return ext if ext != '.jpeg' else '.jpg'
    return '.jpg'  # 默认扩展名

def download_image(url, save_path):
    """下载单个图片"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=30) as response:
            with open(save_path, 'wb') as f:
                f.write(response.read())
        return True
    except Exception as e:
        print(f"  下载失败: {e}")
        return False

def main():
    # 读取原始数据
    data_path = os.path.join(root_dir, 'app', 'src', 'data', 'shijingData.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 图片保存目录
    img_dir = os.path.join(root_dir, 'data', 'img')
    public_img_dir = os.path.join(root_dir, 'app', 'public', 'img')
    
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(public_img_dir, exist_ok=True)
    
    print(f"开始下载图片...")
    print(f"图片保存目录: {img_dir}")
    print(f"前端图片目录: {public_img_dir}")
    print()
    
    success_count = 0
    failed_count = 0
    empty_count = 0
    
    for item in data:
        item_id = item.get('id', 'unknown')
        name = item.get('name', 'unknown')
        image_url = item.get('imageUrl', '')
        
        if not image_url:
            empty_count += 1
            continue
        
        # 生成文件名：id_名称.扩展名
        ext = get_file_extension(image_url)
        safe_name = name.replace('/', '_').replace('\\', '_')
        filename = f"{item_id}_{safe_name}{ext}"
        
        local_path = os.path.join(img_dir, filename)
        public_path = os.path.join(public_img_dir, filename)
        
        print(f"[{item_id}] {name}")
        print(f"  URL: {image_url[:60]}...")
        
        # 下载图片
        if download_image(image_url, local_path):
            # 复制到 public 目录
            import shutil
            shutil.copy2(local_path, public_path)
            
            # 更新数据中的图片路径为本地路径
            item['imageUrl'] = f"/img/{filename}"
            success_count += 1
            print(f"  ✓ 已下载: {filename}")
        else:
            failed_count += 1
            # 下载失败时清空 URL，使用占位图
            item['imageUrl'] = ''
        print()
    
    # 保存更新后的数据
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("=" * 50)
    print(f"下载完成!")
    print(f"  成功: {success_count}")
    print(f"  失败: {failed_count}")
    print(f"  空URL: {empty_count}")
    print(f"  总计: {len(data)}")
    print()
    print(f"数据文件已更新: {data_path}")

if __name__ == '__main__':
    main()
