from functools import partial
from itertools import groupby
from heapq import merge


def key_zipper(key, *iterables):
    """Similar to zip function, but zips backed on some key function.
    If a key exist in some iterables but not others, `None` alongside values that do match that ID.
    IDs must be unique within a single iterable."""
    indexed_iterables = [
        [(i, v) for v in iterable] for i, iterable in enumerate(iterables)
    ]
    value_len = len(indexed_iterables)

    def new_key(x):
        return key(x[1])

    sorted_by_key = partial(sorted, key=new_key)
    for k, values in groupby(
        merge(*map(sorted_by_key, indexed_iterables), key=new_key), key=new_key
    ):
        result = [None] * value_len
        for index, value in values:
            result[index] = value
        yield result
