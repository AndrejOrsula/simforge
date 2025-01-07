from typing import Annotated, Dict, List, TypeAlias

from annotated_types import Len
from pydantic import InstanceOf, NonNegativeInt, PositiveInt

from simforge._typing.enum import EnumNameSerializer
from simforge.core.asset.asset_type import AssetType
from simforge.core.baker import BakeType
from simforge.core.exporter import Exporter, FileFormat

FileFormatConfig: TypeAlias = (
    InstanceOf[FileFormat]
    | Annotated[
        List[InstanceOf[FileFormat]], Len(min_length=1, max_length=len(AssetType))
    ]
    | None
)

ExporterConfig: TypeAlias = (
    InstanceOf[Exporter]
    | Annotated[
        List[InstanceOf[Exporter]], Len(min_length=1, max_length=len(AssetType))
    ]
    | Annotated[
        Dict[Annotated[AssetType, EnumNameSerializer], InstanceOf[Exporter]],
        Len(min_length=1, max_length=len(AssetType)),
    ]
)

TexResConfig: TypeAlias = (
    NonNegativeInt
    | Annotated[
        Dict[Annotated[BakeType, EnumNameSerializer], PositiveInt],
        Len(min_length=1, max_length=len(BakeType)),
    ]
)
