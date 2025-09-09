
from functools import lru_cache

@lru_cache
def fetchFile(filePath: str):
    data = None
    with open(filePath, 'r') as file:
        data = file.read()

    return data
