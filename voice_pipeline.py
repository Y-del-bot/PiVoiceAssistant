"""任务4：语音输入 -> 百度语音识别 -> 大模型输出对话结果。

流程:
  1. USB摄像头麦克风录音5秒（16000Hz单声道）
  2. 百度语音识别API转写为文字
  3. 文字发送给OpenRouter免费大模型
  4. 打印大模型的中文回复

运行: PYTHONIOENCODING=utf-8 python voice_pipeline.py
"""

import base64
import os
import sys
import time
import wave

import pyaudio
import requests

# 安全提示：以下占位符请换成你自己的密钥，且不要把真实密钥提交到公开仓库
LLM_API_KEY = "YOUR_OPENROUTER_API_KEY"
LLM_API_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
BAIDU_API_KEY = "YOUR_BAIDU_API_KEY"
BAIDU_SECRET_KEY = "YOUR_BAIDU_SECRET_KEY"
BAIDU_TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
BAIDU_ASR_URL = "https://vop.baidu.com/server_api"

# ====== 录音参数（该USB麦克风实测只支持16000Hz单声道） ======
RATE = 16000
CHANNELS = 1
CHUNK = 1024
RECORD_SECONDS = 5
RECORD_FILE = "recording.wav"


def record_wav(path: str = RECORD_FILE) -> None:
    """从USB摄像头麦克风录音5秒并保存为WAV。"""
    pa = pyaudio.PyAudio()
    try:
        dev = None
        inputs = [
            pa.get_device_info_by_index(i)
            for i in range(pa.get_device_count())
            if pa.get_device_info_by_index(i).get("maxInputChannels", 0) > 0
        ]
        for info in inputs:
            name = str(info["name"]).lower()
            if "usb" in name or "camera" in name:
                dev = info
                break
        if dev is None:
            dev = pa.get_default_input_device_info()

        print(f"[信息] 录音设备: [{dev['index']}] {dev['name']}")
        print(f"[信息] 开始录音 {RECORD_SECONDS} 秒...（请说话）")
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=int(dev["index"]),
            frames_per_buffer=CHUNK,
        )
        frames = []
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            frames.append(stream.read(CHUNK, exception_on_overflow=False))
        stream.stop_stream()
        stream.close()

        with wave.open(path, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
    finally:
        pa.terminate()
    print(f"[信息] 录音完成: {path}")


def get_baidu_token() -> str:
    """用APIKey/SecretKey换取百度access_token。"""
    resp = requests.post(
        BAIDU_TOKEN_URL,
        params={
            "grant_type": "client_credentials",
            "client_id": BAIDU_API_KEY,
            "client_secret": BAIDU_SECRET_KEY,
        },
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json().get("access_token")
    if not token:
        raise RuntimeError(f"获取百度token失败: {resp.text}")
    return token


def baidu_asr(wav_path: str, token: str) -> str:
    """把WAV音频发给百度短语音识别，返回识别文本。"""
    with open(wav_path, "rb") as f:
        speech = base64.b64encode(f.read()).decode("utf-8")

    resp = requests.post(
        BAIDU_ASR_URL,
        json={
            "format": "wav",
            "rate": RATE,
            "channel": 1,
            "cuid": "raspberrypi",
            "token": token,
            "speech": speech,
            "len": os.path.getsize(wav_path),
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("err_no") != 0:
        raise RuntimeError(f"百度识别失败({data.get('err_no')}): {data.get('err_msg')}")
    return data["result"][0]


def ask_llm(text: str) -> str:
    """把识别出的文字发给OpenRouter大模型，返回回复。"""
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": "你是一个语音助手，请用简洁的中文回答。"},
            {"role": "user", "content": text},
        ],
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    # 免费模型偶发限流(429/502/503)，自动重试最多3次
    data = None
    for attempt in range(1, 4):
        resp = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=120)
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
        raise RuntimeError(f"大模型回复格式异常: {data}")


def main() -> int:
    try:
        # 第1步：录音
        record_wav()

        # 第2步：百度语音识别
        print("[信息] 正在调用百度语音识别...")
        token = get_baidu_token()
        text = baidu_asr(RECORD_FILE, token)
        print(f"[信息] 识别结果: {text}")

        # 第3步：大模型对话
        print("[信息] 正在请求大模型...")
        answer = ask_llm(text)

        # 第4步：输出
        print("[信息] 大模型回复：")
        print(answer)
        return 0
    except RuntimeError as e:
        print(f"[错误] {e}")
        return 1
    except requests.RequestException as e:
        print(f"[错误] 网络请求失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
