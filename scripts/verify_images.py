#!/usr/bin/env python3
"""
验证 shijing_things.json 中的图片是否与 description 描述一致
使用 Kimi 多模态 API 进行检查

用法:
    export KIMI_API_KEY="your_api_key"
    python scripts/verify_images.py
    
    # 验证特定ID范围
    python scripts/verify_images.py --start-id 1 --end-id 50
    
    # 从失败记录中重新验证
    python scripts/verify_images.py --retry-failed
"""
import os
import sys
import json
import base64
import time
import argparse
from pathlib import Path
from typing import Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_json(path: Path) -> dict | list:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path: Path, data: dict | list):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def encode_image_to_base64(image_path: Path) -> str:
    """将图片编码为 base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def get_image_mime_type(image_path: Path) -> str:
    """获取图片的 MIME 类型"""
    suffix = image_path.suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.gif': 'image/gif',
    }
    return mime_types.get(suffix, 'image/jpeg')


def verify_image_with_kimi(
    api_key: str,
    name: str,
    description: str,
    image_path: Path,
    model: str = "moonshot-v1-32k-vision-preview"
) -> dict:
    """
    使用 Kimi 多模态 API 验证图片与描述是否匹配
    
    Returns:
        {
            "matched": bool,
            "confidence": str,  # "high" | "medium" | "low"
            "reason": str,
            "raw_response": str
        }
    """
    try:
        # 读取并编码图片
        image_base64 = encode_image_to_base64(image_path)
        mime_type = get_image_mime_type(image_path)
        
        # 构建提示词
        system_prompt = """你是一个专业的诗经植物和动物识别专家。你的任务是判断提供的图片是否符合给定的名称和描述。

请仔细分析图片内容，判断：
1. 图片中的物体是否与名称相符
2. 图片中的物体是否与描述相符

回答格式：
- 首先给出判断结果："匹配"/"不匹配"/"不确定"
- 然后给出置信度："高"/"中"/"低"
- 最后给出简要理由（50字以内）

示例回答：
匹配
高
图片显示的是黄色的小米穗，与"稷（粟）"的描述"粟（小米），百谷之长"完全一致。"""

        user_prompt = f"名称：{name}\n描述：{description}\n\n请判断上方图片是否符合上述名称和描述。"
        
        # 调用 Kimi API
        import requests
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        response = requests.post(
            "https://api.moonshot.cn/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()
        
        # 解析结果
        lines = content.split('\n')
        matched_str = lines[0].strip() if lines else "不确定"
        confidence = lines[1].strip() if len(lines) > 1 else "低"
        reason = lines[2].strip() if len(lines) > 2 else content[:100]
        
        matched = matched_str in ["匹配", "是", "符合", "正确"]
        not_matched = matched_str in ["不匹配", "否", "不符合", "错误"]
        
        return {
            "matched": matched,
            "not_matched": not_matched,
            "confidence": confidence.lower() if confidence.lower() in ["high", "medium", "low", "高", "中", "低"] else "low",
            "reason": reason,
            "raw_response": content
        }
        
    except Exception as e:
        return {
            "matched": False,
            "not_matched": False,
            "confidence": "low",
            "reason": f"API调用失败: {str(e)}",
            "raw_response": str(e),
            "error": True
        }


def main():
    parser = argparse.ArgumentParser(description='验证图片与描述是否匹配')
    parser.add_argument('--start-id', type=int, default=1, help='起始ID')
    parser.add_argument('--end-id', type=int, default=9999, help='结束ID')
    parser.add_argument('--retry-failed', action='store_true', help='重新验证之前失败的')
    parser.add_argument('--delay', type=float, default=1.0, help='API调用间隔(秒)')
    parser.add_argument('--output', type=str, default='scripts/verify_results.json', help='结果输出文件')
    args = parser.parse_args()
    
    # 检查 API key
    api_key = "sk-kimi-sUI3ZYVC29gwZlXmbOP1aZCaBZ6feNso6SaR4VRopatSHxe4KZTarhXUgLw6cYKK"
    if not api_key:
        print("错误: 请设置环境变量 KIMI_API_KEY")
        print("  export KIMI_API_KEY='your_api_key'")
        sys.exit(1)
    
    # 加载数据
    root_dir = Path(__file__).parent.parent
    data_dir = root_dir / 'data'
    img_dir = root_dir / 'shijing_things' / 'static' / 'img'
    
    things = load_json(data_dir / 'shijing_things.json')
    
    # 加载之前的结果（如果有）
    results_file = Path(args.output)
    previous_results = {}
    if results_file.exists():
        previous_results = {r['id']: r for r in load_json(results_file)}
        print(f"加载了 {len(previous_results)} 条之前的验证结果")
    
    # 筛选需要验证的条目
    to_verify = []
    for item in things:
        item_id = item['id']
        if item_id < args.start_id or item_id > args.end_id:
            continue
        if not item.get('image_url'):
            continue
        
        # 如果指定了 --retry-failed，只验证之前失败的
        if args.retry_failed:
            if item_id in previous_results:
                prev = previous_results[item_id]
                if prev.get('matched') or prev.get('error'):
                    continue
            else:
                continue
        
        to_verify.append(item)
    
    print(f"需要验证 {len(to_verify)} 条数据")
    print(f"ID范围: {args.start_id} - {args.end_id}")
    print("=" * 60)
    
    # 开始验证
    results = []
    mismatches = []
    errors = []
    
    for i, item in enumerate(to_verify, 1):
        item_id = item['id']
        name = item['name']
        description = item.get('description', '')
        image_url = item.get('image_url', '')
        
        # 构建图片路径
        if image_url.startswith('/static/'):
            image_path = root_dir / 'shijing_things' / image_url.lstrip('/')
        else:
            image_path = img_dir / image_url
        
        print(f"\n[{i}/{len(to_verify)}] ID={item_id}, 名称={name}")
        print(f"  描述: {description}")
        print(f"  图片: {image_path}")
        
        if not image_path.exists():
            print(f"  ❌ 图片不存在")
            errors.append({
                'id': item_id,
                'name': name,
                'error': '图片文件不存在',
                'path': str(image_path)
            })
            continue
        
        # 调用 API
        result = verify_image_with_kimi(api_key, name, description, image_path)
        result['id'] = item_id
        result['name'] = name
        result['description'] = description
        result['image_path'] = str(image_path)
        
        results.append(result)
        
        # 输出结果
        if result.get('error'):
            print(f"  ❌ 错误: {result['reason']}")
            errors.append(result)
        elif result['matched']:
            print(f"  ✅ 匹配 ({result['confidence']})")
            print(f"     理由: {result['reason']}")
        elif result['not_matched']:
            print(f"  ❌ 不匹配 ({result['confidence']})")
            print(f"     理由: {result['reason']}")
            mismatches.append(result)
        else:
            print(f"  ⚠️  不确定 ({result['confidence']})")
            print(f"     理由: {result['reason']}")
        
        # 保存中间结果
        if i % 10 == 0:
            save_json(results_file, results)
            print(f"  (已保存 {i} 条结果)")
        
        # 延迟
        if i < len(to_verify):
            time.sleep(args.delay)
    
    # 保存最终结果
    save_json(results_file, results)
    
    # 输出统计
    print("\n" + "=" * 60)
    print("验证完成!")
    print(f"总计验证: {len(results)}")
    print(f"  ✅ 匹配: {sum(1 for r in results if r.get('matched'))}")
    print(f"  ❌ 不匹配: {len(mismatches)}")
    print(f"  ⚠️  不确定/错误: {len(errors)}")
    
    # 输出不匹配的详细信息
    if mismatches:
        print("\n不匹配的条目:")
        for m in mismatches:
            print(f"  ID={m['id']}, {m['name']}")
            print(f"    描述: {m['description']}")
            print(f"    理由: {m['reason']}")
    
    print(f"\n结果已保存到: {results_file}")


if __name__ == '__main__':
    main()
