import sys
from pathlib import Path

from ocr_tool import resources
from ocr_tool.resources import resource_path


def test_source_tree_resolves_against_the_repo_root():
    expected = Path(resources.__file__).resolve().parent.parent / "assets" / "app.ico"

    assert resource_path("assets/app.ico") == expected


def test_frozen_resolves_against_the_unpacked_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert resource_path("assets/app.ico") == tmp_path / "assets" / "app.ico"


def test_frozen_without_unpacked_dir_falls_back_next_to_the_exe(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "screenshot-ocr.exe"))

    assert resource_path("assets/app.ico") == tmp_path / "assets" / "app.ico"
