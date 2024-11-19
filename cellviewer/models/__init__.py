from time import time


def file_path(instance, filename) -> str:
    return f"saved_job/{instance.user.id}/{filename}_{int(time())}"