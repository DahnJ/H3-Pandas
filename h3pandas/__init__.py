from . import h3pandas  # noqa: F401s

from ._version import get_versions

__version__ = get_versions()["version"]
del get_versions
