import platform
import pathlib

from ithaca.settings import CACHE_DIR


def get_cache_dir() -> pathlib.Path:
    """
    Create or get the cache directory.
    """
    if CACHE_DIR and pathlib.Path(CACHE_DIR).exists() and pathlib.Path(CACHE_DIR).is_dir():
        return pathlib.Path(CACHE_DIR)
    
    if platform.system() == "Windows":
        cache_dir = pathlib.Path.home() / "AppData" / "Local" / "ithaca"
    else:
        cache_dir = pathlib.Path.home() / ".cache" / "ithaca"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


