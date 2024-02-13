from typing import List, TypeVar

NumConstructor = TypeVar("NumConstructor")


def line_as_numbers(line: str, indices: List[int], number_constructor: NumConstructor = int) -> List[NumConstructor]:
    """
    Extracts the given `indices` from `line` as a list of numbers.

    You can use a custom constructor (e.g. `float`) with `number_constructor`.
    """
    parts = line.split()
    return [number_constructor(parts[index]) for index in indices]
