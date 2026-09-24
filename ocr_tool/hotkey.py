"""全局**热键**的解析与换算。Windows 无关的纯逻辑集中在这里，便于测试。"""

from PySide6.QtCore import Qt

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

_MODIFIER_ALIASES = {
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "win": "Win",
    "meta": "Win",
    "super": "Win",
}

_MODIFIER_ORDER = ("Ctrl", "Alt", "Shift", "Win")

_MODIFIER_BITS = {
    "Ctrl": MOD_CONTROL,
    "Alt": MOD_ALT,
    "Shift": MOD_SHIFT,
    "Win": MOD_WIN,
}

_QT_MODIFIERS = (
    (Qt.KeyboardModifier.ControlModifier, "Ctrl"),
    (Qt.KeyboardModifier.AltModifier, "Alt"),
    (Qt.KeyboardModifier.ShiftModifier, "Shift"),
    (Qt.KeyboardModifier.MetaModifier, "Win"),
)

_QT_KEYS = {
    Qt.Key.Key_Space: "Space",
    Qt.Key.Key_Tab: "Tab",
    Qt.Key.Key_Return: "Enter",
    Qt.Key.Key_Enter: "Enter",
    Qt.Key.Key_Backspace: "Backspace",
    Qt.Key.Key_Delete: "Delete",
    Qt.Key.Key_Insert: "Insert",
    Qt.Key.Key_Home: "Home",
    Qt.Key.Key_End: "End",
    Qt.Key.Key_PageUp: "PageUp",
    Qt.Key.Key_PageDown: "PageDown",
    Qt.Key.Key_Left: "Left",
    Qt.Key.Key_Right: "Right",
    Qt.Key.Key_Up: "Up",
    Qt.Key.Key_Down: "Down",
}
for _index in range(1, 25):
    _QT_KEYS[getattr(Qt.Key, f"Key_F{_index}")] = f"F{_index}"
for _letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    _QT_KEYS[getattr(Qt.Key, f"Key_{_letter}")] = _letter
for _digit in "0123456789":
    _QT_KEYS[getattr(Qt.Key, f"Key_{_digit}")] = _digit

_NAMED_VIRTUAL_KEYS = {
    "Space": 0x20,
    "Tab": 0x09,
    "Enter": 0x0D,
    "Backspace": 0x08,
    "Delete": 0x2E,
    "Insert": 0x2D,
    "Home": 0x24,
    "End": 0x23,
    "PageUp": 0x21,
    "PageDown": 0x22,
    "Left": 0x25,
    "Right": 0x27,
    "Up": 0x26,
    "Down": 0x28,
}

_MODIFIER_KEYS = {
    Qt.Key.Key_Control,
    Qt.Key.Key_Shift,
    Qt.Key.Key_Alt,
    Qt.Key.Key_Meta,
}


_LETTERS_AND_DIGITS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")


def combination_from(modifiers, key) -> str | None:
    """把 Qt 的修饰键与主键翻译成「Ctrl+Alt+O」这样的写法。"""
    if key in _MODIFIER_KEYS:
        return None
    if not any(modifiers & flag for flag, _ in _QT_MODIFIERS):
        return None
    name = _QT_KEYS.get(key)
    if name is None:
        return None
    parts = [label for flag, label in _QT_MODIFIERS if modifiers & flag]
    parts.append(name)
    return normalize("+".join(parts))


def split(text: str) -> tuple[list[str], str] | None:
    """拆出修饰键列表与主键名；含无法识别的内容时返回 None。"""
    pieces = [piece.strip() for piece in text.split("+") if piece.strip()]
    if len(pieces) < 2:
        return None
    modifiers: list[str] = []
    for piece in pieces[:-1]:
        canonical = _MODIFIER_ALIASES.get(piece.lower())
        if canonical is None or canonical in modifiers:
            return None
        modifiers.append(canonical)
    key = _canonical_key(pieces[-1])
    if key is None:
        return None
    return modifiers, key


def normalize(text: str) -> str:
    """统一大小写与顺序；无法识别时原样返回。"""
    parsed = split(text)
    if parsed is None:
        return text.strip()
    modifiers, key = parsed
    ordered = [name for name in _MODIFIER_ORDER if name in modifiers]
    return "+".join([*ordered, key])


def is_valid(text: str) -> bool:
    return split(text) is not None


def win_parts(text: str) -> tuple[int, int]:
    """换算成 Windows `RegisterHotKey` 需要的（修饰位, 虚拟键码）。"""
    parsed = split(text)
    if parsed is None:
        raise ValueError(f"无法识别的热键：{text!r}")
    modifiers, key = parsed
    bits = 0
    for name in modifiers:
        bits |= _MODIFIER_BITS[name]
    return bits, _virtual_key(key)


def _canonical_key(piece: str) -> str | None:
    candidate = piece.upper()
    if len(candidate) == 1 and candidate in _LETTERS_AND_DIGITS:
        return candidate
    if candidate.startswith("F") and candidate[1:].isdigit():
        if 1 <= int(candidate[1:]) <= 24:
            return candidate
    for name in _NAMED_VIRTUAL_KEYS:
        if name.upper() == candidate:
            return name
    return None


def _virtual_key(key: str) -> int:
    if len(key) == 1:
        return ord(key)
    if key.startswith("F") and key[1:].isdigit():
        return 0x70 + int(key[1:]) - 1
    return _NAMED_VIRTUAL_KEYS[key]
