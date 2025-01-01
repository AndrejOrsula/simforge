from pathlib import Path

from pydantic import BaseModel


class Renderer(BaseModel, defer_build=True):
    def __new__(cls, *args, **kwargs):
        if cls == Renderer:
            raise TypeError(f"Cannot instantiate abstract class {cls.__name__}")
        return super().__new__(cls)

    def setup(self):
        pass

    def render(self, filepath: Path):
        raise NotImplementedError
