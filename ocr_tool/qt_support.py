"""Qt 后台线程的公共支撑。"""

_RUNNING_WORKERS: set = set()


def describe(exc: BaseException) -> str:
    """把异常变成能给用户看的一句话。"""
    return str(exc).strip() or type(exc).__name__


def keep_alive(worker) -> None:
    """在后台线程结束前持有它的引用，避免对象被回收导致进程崩溃。"""
    _RUNNING_WORKERS.add(worker)
    worker.finished.connect(lambda: _RUNNING_WORKERS.discard(worker))
