from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("xiaomi-speaker")
except PackageNotFoundError:
    __version__ = "unknown"
