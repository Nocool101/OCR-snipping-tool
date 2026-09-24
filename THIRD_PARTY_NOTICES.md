# 第三方组件声明（Third-Party Notices）

本软件（截图识别 / screenshot-ocr）使用了以下第三方开源组件，感谢原作者的贡献。各组件遵从其自身的许可证分发，本文件仅作汇总说明。

## 运行期依赖

### PySide6

- **版本**：6.10.2
- **用途**：GUI 框架（窗口、托盘、截图浮层）
- **许可证**：GNU Lesser General Public License v3.0 (LGPL v3)
- **来源**：https://www.qt.io/developers / https://pypi.org/project/PySide6/
- **说明**：本软件通过 PyInstaller 将 PySide6 打包 exe 分发，此分发方式符合 Qt for Python 官方对 LGPL v3 的使用规定。本软件自身源码以 MIT 许可证开放，交付对应 LGPL 库替换要求的方式即为本仓库源码。如需获取 PySide6 独立来源或了解其许可详情，请访问 Qt 官网。
- LGPL v3 许可证文本：https://www.gnu.org/licenses/lgpl-3.0.html

## 构建期依赖（仅打包时使用，不随运行时分发）

### Pillow

- **版本**：12.3.0
- **用途**：生成应用图标 `assets/app.ico`（见 `packaging/make_icon.py`），运行期不使用
- **许可证**：MIT-CMU（HPND 类许可，性质类 MIT，宽松）
- **来源**：https://python-pillow.org / https://pypi.org/project/pillow/
- 许可证文本摘录：

```
The Python Imaging Library (PIL) is

    Copyright © 1997-2011 by Secret Labs AB
    Copyright © 1995-2011 by Fredrik Lundh
    Copyright © 2016-2024 by Alex Clark and contributors

Pillow is the friendly PIL fork. Pillow is open source software, licensed under the MIT-CMU license.
```

### PyInstaller

- **版本**：6.22.3
- **用途**：将 Python 程序打包为 Windows 单文件 exe
- **许可证**：GPL v2 或更新版本，**附带 bootloader 特殊例外**——PyInstaller 官方明确允许使用其 bootloader 打包的应用以任意许可证分发，不被 GPL 传染
- **来源**：https://pyinstaller.org / https://pypi.org/project/pyinstaller/

## 本软件

截图识别（screenshot-ocr）本体以 **MIT License** 许可发布，见仓库根目录的 [`LICENSE`](LICENSE) 文件。

Copyright (c) 2026 Nocool101
