from PySide6.QtCore import Qt

from ocr_tool.hotkey import combination_from, is_valid, normalize, win_parts


def test_normalize_canonicalizes_case_and_order():
    assert normalize("ctrl+alt+o") == "Ctrl+Alt+O"
    assert normalize("ALT+CTRL+O") == "Ctrl+Alt+O"
    assert normalize(" Control + Shift + F5 ") == "Ctrl+Shift+F5"


def test_normalize_maps_meta_aliases_to_win():
    assert normalize("win+o") == "Win+O"
    assert normalize("super+o") == "Win+O"
    assert normalize("meta+o") == "Win+O"


def test_a_hotkey_needs_at_least_one_modifier_and_one_key():
    assert is_valid("Ctrl+Alt+O") is True
    assert is_valid("Ctrl+O") is True
    assert is_valid("O") is False
    assert is_valid("Ctrl+Alt") is False
    assert is_valid("Ctrl+Alt+NotAKey") is False
    assert is_valid("") is False


def test_combination_from_reads_qt_modifiers_and_key():
    modifiers = (
        Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier
    )

    assert combination_from(modifiers, Qt.Key.Key_O) == "Ctrl+Alt+O"


def test_combination_from_needs_a_real_key():
    assert combination_from(Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Control) is None
    assert combination_from(Qt.KeyboardModifier.ControlModifier, Qt.Key.Key_Shift) is None


def test_combination_from_requires_a_modifier():
    assert combination_from(Qt.KeyboardModifier.NoModifier, Qt.Key.Key_O) is None


def test_non_ascii_characters_are_not_accepted_as_keys():
    assert is_valid("Ctrl+我") is False
    assert is_valid("Ctrl+é") is False


def test_win_parts_maps_modifiers_and_virtual_keys():
    mods, vk = win_parts("Ctrl+Alt+O")

    assert mods == 0x0002 | 0x0001
    assert vk == ord("O")


def test_win_parts_handles_function_and_named_keys():
    mods, vk = win_parts("Ctrl+F5")
    assert mods == 0x0002
    assert vk == 0x74

    mods, vk = win_parts("Win+Shift+Space")
    assert mods == 0x0008 | 0x0004
    assert vk == 0x20
