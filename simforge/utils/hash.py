import hashlib
from functools import cache

from pydantic import BaseModel

from simforge.utils import logging


def md5_hexdigest_from_pydantic(*models: BaseModel) -> str:
    return md5_hexdigest_from_str(
        "[" + ",".join((model.model_dump_json() for model in models)) + "]"
    )


@cache
def md5_hexdigest_from_str(input: str) -> str:
    return md5_hexdigest_from_bytes(input.encode())


def md5_hexdigest_from_bytes(data: bytes, len: int = 12) -> str:
    hexdigest = hashlib.md5(data, usedforsecurity=False).hexdigest()[:len]
    logging.debug(f"Hash: {hexdigest} ~ {data}")
    return hexdigest
