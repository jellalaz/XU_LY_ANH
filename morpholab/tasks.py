"""Hủy tác vụ có phối hợp giữa giao diện, thuật toán và tiến trình con."""
from contextlib import contextmanager
import threading


class Cancelled(RuntimeError):
    pass


class Cancellation:
    def __init__(self): self.event=threading.Event()
    def cancel(self): self.event.set()
    def check(self):
        if self.event.is_set(): raise Cancelled('Đã dừng tác vụ theo yêu cầu.')


_local=threading.local()


def check_cancelled():
    """Kiểm tra yêu cầu hủy ở các điểm an toàn trong tác vụ."""
    token=getattr(_local,'token',None)
    if token is not None: token.check()


@contextmanager
def task_scope(token):
    previous=getattr(_local,'token',None)
    _local.token=token
    try:
        token.check()
        yield
    finally: _local.token=previous
