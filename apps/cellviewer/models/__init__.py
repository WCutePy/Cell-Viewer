from time import time


def file_path(instance, filename) -> str:
    return f"saved_file/{filename}_{int(time())}"
