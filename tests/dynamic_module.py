"""A module that delays importing `time` until after it's convenient for
freezegun"""

time_after_start = None

def add_after_start() -> None:
    import time
    import sys

    global time_after_start
    time_after_start = time.time()
    setattr(sys.modules[__name__], 'dynamic_time', time.time())
    setattr(sys.modules[__name__], 'dynamic_time_func', time.time)
