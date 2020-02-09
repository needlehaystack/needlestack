import threading
from functools import wraps
from typing import Dict, Callable


def multiton_pattern(create_fn: Callable) -> Callable:
    lock = threading.Lock()
    cache: Dict[str, object] = {}

    @wraps(create_fn)
    def getter(*args):
        key = "|".join(map(str, args))
        if key not in cache:
            obj = create_fn(*args)
            with lock:
                cache[key] = obj
        return cache[key]

    return getter
