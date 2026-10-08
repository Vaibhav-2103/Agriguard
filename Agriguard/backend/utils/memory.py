import os
import logging
import psutil

logger = logging.getLogger("agriguard.memory")


def get_process_memory_mb() -> float:
    """Returns current process Resident Set Size (RSS) memory in Megabytes."""
    try:
        process = psutil.Process(os.getpid())
        rss_bytes = process.memory_info().rss
        return round(rss_bytes / (1024 * 1024), 2)
    except Exception as e:
        logger.warning(f"Could not retrieve memory statistics: {e}")
        return 0.0


def log_memory(stage: str):
    """Logs current process RSS memory consumption."""
    rss_mb = get_process_memory_mb()
    logger.info(f"💾 [MEMORY TELEMETRY] {stage}: {rss_mb} MB RSS")
    return rss_mb


log_memory_usage = log_memory

