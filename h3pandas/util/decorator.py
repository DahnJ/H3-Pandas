from functools import wraps
from typing import Callable
from h3 import H3CellError


def catch_invalid_h3_address(f: Callable) -> Callable:
    """Wrapper that catches potential invalid H3 addresses.

    Parameters
    ----------
    f : Callable

    Returns
    -------
    The return value of f, or a ValueError if f threw ValueError, TypeError, or H3CellError

    Raises
    ------
    ValueError
        When an invalid H3 address is encountered
    """

    @wraps(f)
    def safe_f(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except (TypeError, ValueError, H3CellError) as e:
            message = f"H3 method raised an error. Is the H3 address correct?"
            message += f"\nCaller: {f.__name__}({_print_signature(*args, **kwargs)})"
            message += f'\nOriginal error: {repr(e)}'
            raise ValueError(message)

    return safe_f


def _print_signature(*args, **kwargs):
    signature = []
    if args:
        signature.append(', '.join([repr(a) for a in args]))
    if kwargs:
        signature.append(', '.join({f'{repr(k)}={repr(v)}' for k, v in kwargs.items()}))

    return ', '.join(signature)
