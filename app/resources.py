import sys
from pathlib import Path


def asset_path(name: str) -> Path:
    """返回资源文件路径，兼容开发模式与 PyInstaller 打包。"""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parents[1]
    return base / "assets" / name
