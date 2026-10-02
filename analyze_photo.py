#!/usr/bin/env python3
"""任务3-后半：把 photo.jpg 发给多模态大模型，输出中文识别结果（单轮，不打印推理过程）。

流程: 读取 photo.jpg -> base64编码 -> OpenRouter视觉模型 -> 只打印中文 content
运行: python analyze_photo.py
"""
import base64
import os
import sys
import time

import requests

# 安全提示：请把下面的占位符换成你自己的 API Key，且不要把真实 Key 提交到公开仓库
API_KEY = "YOUR_OPENROUTER_API_KEY"
MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
PHOTO_FILE = "photo.jpg"
PROMPT = "请用中文描述这张照片里有什么内容，简洁回答。"


def ask_vision_model(image_path: str) -> str:
    """把照片发给多模态模型，只返回最终中文回复（不取 reasoning 推理过程）。"""
    if not os.path.exists(image_path):
        raise RuntimeError(f"找不到图片 {image_path}，请先运行: python capture_photo.py")

    with open(image_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ]},
        ],
    }
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    # 免费模型偶发 429/502/503 限流，自动重试最多3次
    data = None
    for attempt in range(1, 4):
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if resp.status_code in (429, 500, 502, 503):
            print(f"[警告] 模型繁忙(HTTP {resp.status_code})，10秒后第{attempt + 1}次尝试...")
            time.sleep(10)
            continue
        resp.raise_for_status()
        data = resp.json()
        break
    if data is None:
        raise RuntimeError("模型连续繁忙，请稍后再试")
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise RuntimeError(f"回复格式异常: {data}")


def main() -> int:
    try:
        print(f"[信息] 正在把 {PHOTO_FILE} 发送给大模型({MODEL})...")
        answer = ask_vision_model(PHOTO_FILE)
    except RuntimeError as e:
        print(f"[错误] {e}")
        return 1
    except requests.RequestException as e:
        print(f"[错误] 网络请求失败: {e}")
        return 1

    print("[信息] 大模型识别结果：")
    print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
