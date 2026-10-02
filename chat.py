#!/usr/bin/env python3
"""树莓派文字问答 - 调用 OpenRouter 免费大模型

运行: python chat.py
输入 quit / 退出 / q 结束对话
"""
import requests

# 安全提示：请把下面的占位符换成你自己的 API Key，且不要把真实 Key 提交到公开仓库
API_KEY = "YOUR_OPENROUTER_API_KEY"
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def chat(question: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个友好的AI助手,请用简洁的中文回答问题。"},
            {"role": "user", "content": question},
        ],
    }
    try:
        resp = requests.post(API_URL, headers=headers, json=data, timeout=120)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError:
        return f"请求失败(HTTP {resp.status_code}): {resp.text[:300]}"
    except Exception as e:
        return f"出错: {e}"


def main() -> None:
    print("=" * 50)
    print("  树莓派文字问答(OpenRouter 免费大模型)")
    print(f"  模型: {MODEL}")
    print("  输入 quit / 退出 / q 结束对话")
    print("=" * 50)
    while True:
        try:
            question = input("\n你: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            continue
        if question.lower() in ("quit", "exit", "退出", "q"):
            print("再见!")
            break
        print("思考中...(免费模型较慢,请耐心等1~2分钟)", flush=True)
        answer = chat(question)
        print(f"\nAI: {answer}")


if __name__ == "__main__":
    main()
