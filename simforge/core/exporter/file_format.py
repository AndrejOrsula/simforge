from __future__ import annotations

from enum import Enum, auto
from typing import ClassVar, Iterable, List, Type

from typing_extensions import Self


class FileFormat(str, Enum):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        FileFormatRegistry.registry.append(cls)

    def __str__(self) -> str:
        return self.name.lower()

    @property
    def ext(self) -> str:
        return f".{self}"

    @classmethod
    def from_ext(cls, ext: str) -> Self | None:
        return next(
            (
                format
                for format in cls
                if (ext[1:] if ext.startswith(".") else ext).upper() == format.name
            ),
            None,
        )

    @staticmethod
    def all_formats() -> Iterable[FileFormat]:
        return (format for formats in FileFormatRegistry.registry for format in formats)

    @classmethod
    def from_ext_any(cls, ext: str) -> FileFormat | None:
        return next(
            (
                format
                for format in cls.all_formats()
                if (ext[1:] if ext.startswith(".") else ext).upper() == format.name
            ),
            None,
        )


class FileFormatRegistry:
    registry: ClassVar[List[Type[FileFormat]]] = []


class ImageFileFormat(FileFormat):
    JPG = auto()
    PNG = auto()

    @classmethod
    def from_ext(cls, ext: str) -> Self | None:
        return super().from_ext(ext)


class MaterialFileFormat(FileFormat):
    MDL = auto()

    @classmethod
    def from_ext(cls, ext: str) -> Self | None:
        return super().from_ext(ext)


class ModelFileFormat(FileFormat):
    ABC = auto()
    FBX = auto()
    GLB = auto()
    GLTF = auto()
    OBJ = auto()
    PLY = auto()
    SDF = auto()
    STL = auto()
    USD = auto()
    USDA = auto()
    USDC = auto()
    USDZ = auto()

    @property
    def ext(self) -> str:
        match self:
            case ModelFileFormat.SDF:
                return ""
            case ModelFileFormat.GLTF:
                return ModelFileFormat.GLB.ext
            case _:
                return super().ext

    @classmethod
    def from_ext(cls, ext: str) -> Self | None:
        return super().from_ext(ext)

    @property
    def supports_material(self) -> bool:
        match self:
            case ModelFileFormat.STL:
                return False
            case _:
                return True
