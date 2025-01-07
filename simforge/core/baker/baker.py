from os import environ
from typing import ClassVar, Dict

from pydantic import BaseModel

from simforge.core.baker import BakeType


class Baker(BaseModel, defer_build=True):
    enabled: ClassVar[bool] = environ.get("SF_BAKER", "true").lower() in ("true", "1")

    def setup(self):
        pass

    def bake(self, texture_resolution: int | Dict[BakeType, int]):
        if self.enabled:
            raise NotImplementedError

    def cleanup(self):
        pass
