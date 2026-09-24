"""指令构造：把一次**识别**或一个**动作**变成交给**模型**的指令。"""

RECOGNIZE_INSTRUCTION = (
    "逐字提取图中全部文字。"
    "保留原有的换行与段落。"
    "只输出文字本身，不要添加任何解释、标题或说明。"
    "图中没有文字时，只输出「（未识别到文字）」。"
)

TRANSLATE_INSTRUCTION = "把下面的文字翻译成中文，只输出译文，不要添加任何解释。"
SUMMARIZE_INSTRUCTION = "用几句话概括下面的内容，只输出概括，不要添加任何解释。"
CONVERT_TABLE_INSTRUCTION = (
    "把下面的内容整理成 Markdown 表格，只输出表格，不要添加任何解释。"
    "若原文没有可整理成表格的结构，就原样输出。"
)
ASK_INSTRUCTION = (
    "根据下面的内容回答我的问题。只输出回答本身，不要重复原文，也不要添加额外说明。"
)


def _with_text(instruction: str, text: str) -> str:
    return f"{instruction}\n\n{text}"


def translate_instruction(text: str) -> str:
    return _with_text(TRANSLATE_INSTRUCTION, text)


def summarize_instruction(text: str) -> str:
    return _with_text(SUMMARIZE_INSTRUCTION, text)


def convert_table_instruction(text: str) -> str:
    return _with_text(CONVERT_TABLE_INSTRUCTION, text)


def ask_instruction(question: str, text: str) -> str:
    return f"{ASK_INSTRUCTION}\n\n问题：{question}\n\n内容：\n{text}"
