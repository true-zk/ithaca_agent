"""
Global logger
"""
import logging

from ithaca.utils import get_cache_dir


def setup_logger() -> logging.Logger:
    """
    Setup the global logger
    """
    cache_dir = get_cache_dir()
    log_file = cache_dir / "ithaca.log"
    log_file.touch(exist_ok=True)

    # configure the logger
    logging.basicConfig(
        level=logging.DEBUG,
        filemode="a",
        filename=log_file,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # create global logger
    logger = logging.getLogger("ithaca")
    logger.setLevel(logging.DEBUG)

    logger.info(f"Cache directory: {cache_dir}")
    logger.info(f"Logger setup completed, logging to {log_file}")
    
    return logger

logger = setup_logger()
