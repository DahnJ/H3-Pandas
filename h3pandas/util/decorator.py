from functools import wraps
from typing import Callable, Iterator


def catch_invalid_h3_address(f: Callable) -> Callable:
    """Wrapper that catches potential invalid H3 addresses.

    Parameters
    ----------
    f : Callable

    Returns
    -------
    The return value of f, or a ValueError if f threw ValueError, TypeError,
    or H3CellError

    Raises
    ------
    ValueError
        When an invalid H3 address is encountered
    """

    @wraps(f)
    def safe_f(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (TypeError, ValueError) as e:
            message = "H3 method raised an error. Is the H3 address correct?"
            message += f"\nCaller: {f.__name__}({_print_signature(*args, **kwargs)})"
            message += f"\nOriginal error: {repr(e)}"
            raise ValueError(message)

    return safe_f


def sequential_deduplication(func: Iterator[str]) -> Iterator[str]:
    """
    Decorator that doesn't permit two consecutive items of an iterator
    to be the same.

    Parameters
    ----------
    f : Callable

    Returns
    -------
    Yields from f, but won't yield two items in a row that are the same.
    """

    def inner(*args):
        iterable = func(*args)
        last = None
        while (cell := next(iterable, None)) is not None:
            if cell != last:
                yield cell
            last = cell

    return inner


# TODO: Test
def doc_standard(column_name: str, description: str) -> Callable:
    """Wrapper to provide a standard apply-to-H3-index docstring"""

    def doc_decorator(f):
        @wraps(f)
        def doc_f(*args, **kwargs):
            return f(*args, **kwargs)

        parameters = f.__doc__ or ""

        doc = f"""Adds the column `{column_name}` {description}. Assumes H3 index.
        {parameters}
        Returns
        -------
        Geo(DataFrame) with `{column_name}` column added

        Raises
        ------
        ValueError
            When an invalid H3 address is encountered
        """

        doc_f.__doc__ = doc
        return doc_f

    return doc_decorator


def _print_signature(*args, **kwargs):
    signature = []
    if args:
        signature.append(", ".join([repr(a) for a in args]))
    if kwargs:
        signature.append(", ".join({f"{repr(k)}={repr(v)}" for k, v in kwargs.items()}))

    return ", ".join(signature)
