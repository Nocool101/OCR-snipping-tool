import traceback

try:
    from ocr_tool.main import main

    raise SystemExit(main())
except SystemExit:
    raise
except BaseException:
    from ocr_tool.paths import default_settings_path

    log_path = default_settings_path().parent / "error.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(traceback.format_exc(), encoding="utf-8")
    raise
