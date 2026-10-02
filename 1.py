"""任务1：从USB摄像头内置麦克风录制5秒音频，保存为WAV格式。

硬件实测参数（arecord --dump-hw-params 确认）：
  - 声卡: card 2 "HD camera" (USB Audio) -> hw:2,0
  - 仅支持 16000Hz、单声道、S16_LE
  - 注意：不支持44100Hz，强行使用会报 PaErrorCode -9997

运行: python 1.py
输出: recording.wav（当前目录）
"""

import sys
import wave

import pyaudio

RATE = 16000          # 该麦克风唯一支持的采样率
CHANNELS = 1          # 单声道
WIDTH = 2             # S16_LE = 16位 = 2字节
RECORD_SECONDS = 5
CHUNK = 1024
OUTPUT_FILE = "recording.wav"


def find_input_device(pa: pyaudio.PyAudio) -> dict:
    """自动检测USB麦克风：优先找名字含 usb/camera 的输入设备。

    找不到时退回系统默认输入设备，再不行就报错退出。
    """
    inputs = []
    for i in range(pa.get_device_count()):
        info = pa.get_device_info_by_index(i)
        if info.get("maxInputChannels", 0) > 0:
            inputs.append(info)

    if not inputs:
        raise RuntimeError("没有检测到任何音频输入设备")

    # 1) 优先匹配USB摄像头麦克风
    for info in inputs:
        name = str(info["name"]).lower()
        if "usb" in name or "camera" in name:
            return info
    # 2) 退回默认输入设备
    try:
        return pa.get_default_input_device_info()
    except Exception:
        return inputs[0]


def main() -> int:
    pa = pyaudio.PyAudio()
    try:
        dev = find_input_device(pa)
        print(f"[信息] 选择的输入设备: [{dev['index']}] {dev['name']}")
        print(f"[信息] 录音参数: 采样率={RATE}Hz, 通道数={CHANNELS}, "
              f"位深=int16, 时长={RECORD_SECONDS}秒")

        stream = pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=int(dev["index"]),
            frames_per_buffer=CHUNK,
        )
    except Exception as e:
        print(f"[错误] 打开录音设备失败: {e}")
        return 1

    print("[信息] 开始录音...（请对着摄像头说话）")
    frames = []
    try:
        for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
    except Exception as e:
        print(f"[错误] 录音过程失败: {e}")
        return 1
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()

    try:
        with wave.open(OUTPUT_FILE, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(WIDTH)
            wf.setframerate(RATE)
            wf.writeframes(b"".join(frames))
    except Exception as e:
        print(f"[错误] 保存WAV文件失败: {e}")
        return 1

    print(f"[信息] 录音完成，已保存为 {OUTPUT_FILE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
