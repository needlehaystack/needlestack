import logging
import functools
from typing import Callable

from grpc._channel import _Rendezvous

logger = logging.getLogger("needlestack")


def unhandled_exception_rpc(response_type: type):
    def wrapper(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapped(self, request, context):
            try:
                return func(self, request, context)
            except _Rendezvous as e:
                logger.error(e)
                context.set_code(e.code())
                context.set_details(e.details())
                return response_type()
            except Exception as e:
                logger.error(e)
                raise e

        return wrapped

    return wrapper
