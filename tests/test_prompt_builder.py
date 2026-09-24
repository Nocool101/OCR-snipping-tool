from ocr_tool.prompt_builder import (
    RECOGNIZE_INSTRUCTION,
    convert_table_instruction,
    summarize_instruction,
    translate_instruction,
)


def test_recognition_instruction_demands_verbatim_extraction():
    assert "逐字" in RECOGNIZE_INSTRUCTION


def test_recognition_instruction_preserves_line_breaks():
    assert "换行" in RECOGNIZE_INSTRUCTION


def test_recognition_instruction_forbids_added_commentary():
    assert "不要添加任何解释" in RECOGNIZE_INSTRUCTION


def test_translate_instruction_asks_for_chinese_and_carries_the_text():
    instruction = translate_instruction("Hello world")

    assert "Hello world" in instruction
    assert "中文" in instruction


def test_summarize_instruction_asks_for_a_brief_summary_and_carries_the_text():
    instruction = summarize_instruction("一段很长的文字")

    assert "一段很长的文字" in instruction
    assert "概括" in instruction


def test_convert_table_instruction_asks_for_a_markdown_table():
    instruction = convert_table_instruction("姓名  年龄")

    assert "姓名  年龄" in instruction
    assert "Markdown" in instruction
    assert "表格" in instruction
