import platform
import pathlib


def get_cache_dir() -> pathlib.Path:
    """
    Create or get the cache directory
    """
    if platform.system() == "Windows":
        cache_dir = pathlib.Path.home() / "AppData" / "Local" / "ithaca"
    else:
        cache_dir = pathlib.Path.home() / ".cache" / "ithaca"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


