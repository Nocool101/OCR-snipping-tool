from ocr_tool.prompt_builder import RECOGNIZE_INSTRUCTION


def test_recognition_instruction_demands_verbatim_extraction():
    assert "逐字" in RECOGNIZE_INSTRUCTION


def test_recognition_instruction_preserves_line_breaks():
    assert "换行" in RECOGNIZE_INSTRUCTION


def test_recognition_instruction_forbids_added_commentary():
    assert "不要添加任何解释" in RECOGNIZE_INSTRUCTION
