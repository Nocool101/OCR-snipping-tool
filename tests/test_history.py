from datetime import datetime

from ocr_tool.history import History, Recognition


def test_history_is_empty_at_first():
    assert History().entries == ()


def test_newest_entry_comes_first():
    history = History()
    older = datetime(2026, 1, 1, 10, 0, 0)
    newer = datetime(2026, 1, 1, 10, 5, 0)

    history.add("第一条", at=older)
    history.add("第二条", at=newer)

    assert [entry.text for entry in history.entries] == ["第二条", "第一条"]


def test_entries_beyond_the_limit_drop_the_oldest():
    history = History(limit=3)

    for index in range(5):
        history.add(f"第{index}条", at=datetime(2026, 1, 1, 10, index))

    texts = [entry.text for entry in history.entries]
    assert texts == ["第4条", "第3条", "第2条"], texts


def test_limit_is_at_least_one():
    history = History(limit=0)

    history.add("唯一的记录")

    assert [entry.text for entry in history.entries] == ["唯一的记录"]


def test_label_shows_time_and_a_single_line_preview():
    entry = Recognition(
        text="第一行\n第二行  很长的内容" + "啊" * 40,
        at=datetime(2026, 1, 1, 9, 8, 7),
    )

    label = entry.label()

    assert label.startswith("09:08:07")
    assert "\n" not in label
    assert "第一行 第二行" in label
    assert len(label) < 50


def test_label_handles_an_empty_recognition():
    entry = Recognition(text="   ", at=datetime(2026, 1, 1, 9, 8, 7))

    assert "（空）" in entry.label()
