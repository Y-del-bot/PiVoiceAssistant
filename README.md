# PiVoiceAssistant - 树莓派语音/视觉助手

课程小项目：在树莓派 3B+ 上通过 USB 摄像头（自带麦克风）实现与大模型的交互，包括文字问答、拍照识图、语音对话三个功能。

## 硬件与系统

- 树莓派 3B+（Raspberry Pi OS，Python 3.13，venv 虚拟环境）
- USB 摄像头（自带麦克风），麦克风实测仅支持 **16000Hz / 单声道 / S16_LE**

## 文件说明

| 文件 | 功能 | 对应任务 |
|---|---|---|
| `1.py` | 从 USB 麦克风录制 5 秒音频，保存为 WAV | 任务1：音频录制 |
| `chat.py` | 终端文字问答，循环调用免费大模型 | 文字问答演示 |
| `capture_photo.py` | 调用 fswebcam 拍摄一帧照片 | 任务3：拍照 |
| `analyze_photo.py` | 把照片发给多模态大模型，输出中文识别结果 | 任务3：图片识别 |
| `voice_pipeline.py` | 录音 → 百度语音识别 → 大模型回答，完整语音对话 | 任务4：语音对话 |

> 任务2（音频直接上传多模态模型分析）因平台对音频/视频输入收费，按老师要求跳过。

## 配置密钥

运行前需要把两个文件里的占位符替换成自己的密钥：

1. **OpenRouter**（https://openrouter.ai 注册，Models 页找带 `:free` 后缀的免费模型）
   - `chat.py` / `analyze_photo.py` / `voice_pipeline.py` 中的 `API_KEY` / `LLM_API_KEY`
2. **百度智能云**（https://cloud.baidu.com 搜索"语音技术"，创建应用后获取）
   - `voice_pipeline.py` 中的 `BAIDU_API_KEY` 和 `BAIDU_SECRET_KEY`

**安全提示：不要把真实密钥提交到 Git 仓库。** 泄露的密钥会被平台自动吊销，也可能被他人盗用产生费用。

## 安装与运行

```bash
# 树莓派上安装依赖
sudo apt install -y fswebcam
pip install pyaudio requests

# 任务1：录音
python 1.py

# 文字问答
PYTHONIOENCODING=utf-8 python chat.py

# 任务3：先拍照，再识别
python capture_photo.py
PYTHONIOENCODING=utf-8 python analyze_photo.py

# 任务4：语音对话（提示录音后对着麦克风说5秒话）
PYTHONIOENCODING=utf-8 python voice_pipeline.py
```

## 实测踩坑记录

- 该 USB 麦克风不支持 44100Hz，强行使用会报 `PaErrorCode -9997`，必须用 16000Hz。
- 运行时输出的大量 ALSA lib 报错是树莓派探测不存在声卡产生的，无害可忽略。
- OpenRouter 免费模型（`:free` 后缀）偶尔返回 429/502 限流，脚本已内置自动重试；免费模型也可能临时下架，报 404/400 时需要更换模型名。
- 通过 SSH 在终端输入中文时，需加 `PYTHONIOENCODING=utf-8` 避免 UnicodeDecodeError。
