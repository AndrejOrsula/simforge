from typing import Dict

from pydantic import BaseModel

from simforge.core.baker import BakeType


class Baker(BaseModel, defer_build=True):
    def setup(self):
        pass

    def bake(self, texture_resolution: int | Dict[BakeType, int]):
        raise NotImplementedError

    def cleanup(self):
        pass
