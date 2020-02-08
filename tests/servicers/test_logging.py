import logging

from needlestack.servicers.logging import get_debug_handler, get_file_handler


def test_get_debug_handler():
    handler = get_debug_handler(
        fmt="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    assert isinstance(handler, logging.StreamHandler)


def test_get_file_handler():
    handler = get_file_handler(
        fmt="%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_file="my.log",
        max_bytes=1024,
        backup_count=1,
    )
    assert isinstance(handler, logging.StreamHandler)
