#!/usr/bin/env python3
"""任务3-前半：从USB摄像头拍摄一帧图片，保存为 photo.jpg。

运行: python capture_photo.py
说明: -S 15 丢弃前15帧等自动曝光稳定；640x480 + jpeg 60 压缩，体积小上传快。
"""
import subprocess
import sys

PHOTO_FILE = "photo.jpg"


def take_photo(path: str = PHOTO_FILE) -> None:
    try:
        result = subprocess.run(
            ["fswebcam", "-S", "15", "-r", "640x480", "--jpeg", "60",
             "--no-banner", path],
            capture_output=True, text=True, timeout=20,
        )
    except FileNotFoundError:
        raise RuntimeError("未安装 fswebcam，请先执行: sudo apt install -y fswebcam")
    if result.returncode != 0:
        raise RuntimeError(f"拍照失败: {result.stderr.strip()}")


def main() -> int:
    try:
        print("[信息] 正在拍照...")
        take_photo()
        print(f"[信息] 照片已保存: {PHOTO_FILE}")
        return 0
    except RuntimeError as e:
        print(f"[错误] {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
