
from typing import List
from pydantic import BaseModel, Fields
from functools import lru_cache

@lru_cache
def fetchFile(filePath: str):
    data = None
    with open(filePath, 'r') as file:
        data = file.read()

    return data


class NewExchange(BaseModel):
    exchangeName: str
    queues: List[str] = Field(default_factory=lambda: ["default"])

