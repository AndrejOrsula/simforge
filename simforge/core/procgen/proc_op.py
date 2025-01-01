from typing import ClassVar

from pydantic import BaseModel

from simforge.core.procgen import OpType


class ProcOp(BaseModel, defer_build=True):
    OP_TYPE: ClassVar[OpType]

    @property
    def is_randomizable(self) -> bool:
        return False

    def setup(self):
        raise NotImplementedError

    def cleanup(self):
        pass

    def seed(self, seed: int):
        if self.is_randomizable:
            raise NotImplementedError
