from . import h3pandas  # noqa: F401s

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("package-name")
except PackageNotFoundError:
    # package is not installed
    pass
