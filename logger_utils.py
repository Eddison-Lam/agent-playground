import logging
import os
from datetime import datetime

def get_logger(name: str, subdir: str = "main", level=logging.INFO):
    """
    get logger
    
    usage:
        logger = get_logger("Main", subdir="main")
        logger = get_logger("RAGManager", subdir="rag")
        logger = get_logger("Tools", subdir="tools")
    """
    log_dir = f"log/{subdir}"
    os.makedirs(log_dir, exist_ok=True)
    
    # one log file per day
    today = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{name.lower()}_{today}.log")
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # prevent duplicate handler
    if not logger.handlers:
        handler = logging.FileHandler(log_file, encoding='utf-8', delay=True)
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger