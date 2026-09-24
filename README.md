# 截图识别（screenshot-ocr）

> 按热键框选屏幕 → 多模态大模型识别文字 → 就地翻译、总结、表格转换、自定义提问。

一个 Windows 上的个人自用工具。它不走传统 OCR，而是把**截图**直接交给一个多模态大模型（OpenAI 兼容接口）识别出**文本**，再对这段文本做后续处理。因此它不打包本地模型，一份依赖都不多背；代价是识别必须联网、按 token 计费。

## 功能

- **全局热键截图**：默认 `Ctrl+Alt+O`，按下后冻结整屏，拖框选区，`Esc` 取消。
- **识别剪贴板图片**：托盘菜单里一键识别；也可先用 `Win+Shift+S` 截图再点它。
- **流式输出**：识别与所有动作都逐字返回，不用干等。
- **结果窗口**：上半区是可编辑的**文本**，下半区渲染 Markdown 答案，底部是自定义提问输入框。
- **四种动作**：翻译成中文、总结、表格转换、自定义提问。
- **文字大小可调**：设置里带实时预览，改大小时已打开的结果窗口同步跟随。
- **历史记录**：托盘菜单可回看本次运行最近 20 条，仅存内存。
- 单实例运行、开机自启、多显示器截屏。

## 下载

从 [Releases](https://github.com/Nocool101/OCR-snipping-tool/releases) 下载 `screenshot-ocr.exe`（单文件绿色版，无需安装 Python），双击运行。

首次启动因为还没有配置文件，会自动弹出**设置**窗口。

## 使用

1. 打开**设置**，填好**模型**信息，再点「测试连接」确认能通：
   - **接口地址**：OpenAI 兼容的 base URL（例如 `https://你的服务/v1`）
   - **API Key**
   - **模型名**：需要具备视觉 / 图片输入能力
2. 按热键 `Ctrl+Alt+O`，拖框选中要识别的区域。
3. 在**结果窗口**里查看、编辑识别出的文本；点动作按钮，或在底部输入你的问题后回车。

托盘图标（右键）里还有：识别剪贴板图片、历史、设置、退出。双击托盘图标可直接打开设置。

## 配置

设置保存在 `%APPDATA%\screenshot-ocr\settings.json`：

| 字段 | 说明 | 默认 |
| --- | --- | --- |
| `base_url` | 模型接口地址（OpenAI 兼容） | `https://api.openai.com/v1` |
| `api_key` | API Key | 空 |
| `model` | 模型名 | 空 |
| `hotkey` | 全局热键 | `Ctrl+Alt+O` |
| `autostart` | 开机自启 | 关 |
| `font_size` | 结果窗口文字大小（pt，8–40） | `14` |

## 从源码运行

要求：Windows + Python 3.10 以上。运行期只需要 PySide6：

```powershell
pip install PySide6
python -m ocr_tool.main
```

也可以双击 `launcher.pyw`（走 `pythonw`，无控制台窗口）。启动时若抛出异常，会写到 `%APPDATA%\screenshot-ocr\error.log`，方便排查双击没反应的问题。

## 构建 exe

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

产物为 `dist\screenshot-ocr.exe`。脚本会安装 `packaging/requirements.txt`、生成图标，再调用 PyInstaller。可用环境变量 `PYTHON` 指定解释器。

## 测试

```powershell
python -m pytest
```

覆盖设置读写、指令构造、控制器、OpenAI 兼容客户端（用本地假 HTTP 服务，不起真实网络）、热键解析、截图裁剪换算、单实例等。Qt 界面不在自动化测试范围内。

## 项目结构

```
ocr_tool/
  main.py            入口：QApplication、单实例、托盘
  tray.py            托盘菜单、热键触发、结果窗口生命周期
  controller.py      行为中枢：识别 / 动作（不依赖 Qt）
  model_client.py    OpenAI 兼容客户端（SSE 流式、失败分类、重试）
  prompt_builder.py  识别与各动作的指令
  capture.py         整屏抓图与选区裁剪（逻辑坐标 → 设备像素）
  overlay.py         全屏框选遮罩
  result_window.py   结果窗口
  settings_window.py 设置窗口
  settings.py        配置读写与默认值
  history.py         内存历史（最新在前，上限 20）
  hotkey.py          热键解析 / 规范化 / 校验
  hotkey_manager.py  全局热键注册（RegisterHotKey）
  single_instance.py 命名互斥量单实例
  autostart.py       开机自启（注册表 Run 项）
  qt_support.py      Qt 公共支撑
tests/               pytest 测试
packaging/           PyInstaller 配置与构建依赖
```

## 设计说明

- 为什么用多模态大模型而不是传统 OCR（Windows OCR / PaddleOCR / OCR API）：见 [`docs/adr/0001-用多模态大模型替代传统-ocr.md`](docs/adr/0001-用多模态大模型替代传统-ocr.md)。
- 领域术语表与整体模型：见 [`CONTEXT.md`](CONTEXT.md)。

## 隐私

- 截图会被发送到你在设置里配置的**模型**服务，仅此一处；本工具没有自己的服务器。
- API Key 以明文保存在本机 `%APPDATA%\screenshot-ocr\settings.json`，介意的话请自行保护该目录。
- **历史记录只存在内存里**，退出即清空，不落盘。

## 已知限制

- 仅支持 Windows。
- 识别质量与速度取决于所选模型；部分模型不支持图片输入。
- 需要联网，按 token 计费。

## 许可

- 本软件（screenshot-ocr）以 [MIT License](LICENSE) 发布，Copyright (c) 2026 Nocool101。
- 所使用的第三方组件及其许可证见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)（含 PySide6 的 LGPL v3 声明）。
