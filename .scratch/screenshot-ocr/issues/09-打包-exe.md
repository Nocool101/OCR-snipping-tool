# 09: 打包 exe

**What to build:** 把整个工具用 PyInstaller 打成双击即用的 exe，不装 Python 也能跑。这是最终交付形态。

**Blocked by:** 04、05、06、07、08

**Status:** ready-for-agent

- [ ] 打包成 exe，在没装 Python 的机器上双击能启动
- [ ] 托盘图标、设置、热键、框选、识别、动作、自定义提问、历史在 exe 里全部可用
- [x] 打包配置（图标、单文件/单目录、数据文件）写好并可在仓库内复现
- [x] exe 运行时不弹出多余的控制台窗口
- [ ] 在真实机器上人工走一遍：截图 → 流式识别 → 四个动作 → 错误提示

## Comments

**实现（agent）**

- `packaging/screenshot-ocr.spec`：PyInstaller 单文件配置，入口 `launcher.pyw`，`console=False`，
  `datas` 打入 `assets/app.ico`，`icon` 指向同一份 ico。
- `build.ps1` + `packaging/requirements.txt`：一条命令复现（装依赖 → 生成图标 → 出 exe）。
- `packaging/make_icon.py` 从 `ocr_tool/icon.py` 的同一份绘制生成 `assets/app.ico`（多尺寸）。
  托盘/窗口/exe 三处共用该图标。
- `ocr_tool/icon.py` 取代 `tray.py` 里内联的 `_make_icon`；`ocr_tool/qt_support.to_png` 收敛重复的
  PNG 编码。
- `ocr_tool/single_instance.py`：按规格「`main` 单实例」用 Windows 命名互斥量限制单开。
- `ocr_tool/resources.py`：`resource_path` 统一源码/冻结两种根目录。

**已在本机验证（agent）**

- `python -m pytest` → 73 passed。
- `build.ps1` 成功产出 `dist/screenshot-ocr.exe`（约 47 MB）；PE OptionalHeader.Subsystem = 2（GUI），
  即双击不弹控制台。
- 启动该 exe，进程持续存活 10s 无崩溃、无 `%APPDATA%\screenshot-ocr\error.log`，托盘常驻正常。

**仍需人工（本机装有 Python，无法覆盖）**

- 在无 Python 的机器上双击启动。
- 走一遍截图 → 流式识别 → 四个动作 → 自定义提问 → 错误提示 → 历史回看。
- 高 DPI / 多显示器下的框选坐标准确性（与票 04 的遗留项一致）。

