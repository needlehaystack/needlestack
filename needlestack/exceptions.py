class SerializationError(ValueError):
    pass


class DeserializationError(ValueError):
    pass


class UnsupportedIndexOperationException(Exception):
    pass


class KnapsackCapacityException(Exception):
    pass


class KnapsackItemException(Exception):
    pass


class DimensionMismatchException(Exception):
    pass
