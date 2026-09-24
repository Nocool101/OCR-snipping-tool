import uuid

from ocr_tool.single_instance import SingleInstance


def _name() -> str:
    return rf"Local\screenshot-ocr-test-{uuid.uuid4().hex}"


def test_first_acquisition_wins():
    first = SingleInstance(_name())

    assert first.acquire() is True
    assert first.is_held is True

    first.release()
    assert first.is_held is False


def test_second_acquisition_is_refused_while_first_holds():
    name = _name()
    first = SingleInstance(name)
    second = SingleInstance(name)
    assert first.acquire() is True

    assert second.acquire() is False
    assert second.is_held is False

    first.release()


def test_lock_is_available_again_after_release():
    name = _name()
    first = SingleInstance(name)
    assert first.acquire() is True
    first.release()

    again = SingleInstance(name)
    assert again.acquire() is True
    again.release()


def test_acquire_is_idempotent_and_release_is_safe():
    instance = SingleInstance(_name())
    assert instance.acquire() is True
    assert instance.acquire() is True

    instance.release()
    instance.release()

    assert instance.is_held is False
