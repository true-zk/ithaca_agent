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


def get_skill_by_file_name(file_name: str) -> str:
    file_path = pathlib.Path(__file__).parent / "skills" / file_name
    if not file_path.exists():
        raise FileNotFoundError(f"Skill file {file_path} not found")
    with open(file_path, "r") as f:
        return f.read()