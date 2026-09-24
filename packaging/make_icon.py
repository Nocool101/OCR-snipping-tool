"""从 `ocr_tool.icon` 的设计生成 `assets/app.ico`（exe、托盘、窗口共用）。

用法：python packaging/make_icon.py
依赖：PySide6、Pillow（见 packaging/requirements.txt）。
"""

import io
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image  # noqa: E402
from PySide6.QtGui import QGuiApplication  # noqa: E402

from ocr_tool.icon import icon_pixmap  # noqa: E402
from ocr_tool.qt_support import to_png  # noqa: E402

SIZES = (16, 24, 32, 48, 64, 128, 256)
TARGET = REPO_ROOT / "assets" / "app.ico"


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication([])  # noqa: F841

    master = icon_pixmap(max(SIZES))
    image = Image.open(io.BytesIO(to_png(master.toImage())))
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    image.save(TARGET, format="ICO", sizes=[(size, size) for size in SIZES])
    print(f"已生成 {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
