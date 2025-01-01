from typing import Annotated, Dict, List, TypeAlias

from annotated_types import MinLen
from pydantic import InstanceOf, PositiveInt

from simforge._typing.enum import EnumNameSerializer
from simforge.core.asset.asset_type import AssetType
from simforge.core.baker import BakeType
from simforge.core.exporter import Exporter, FileFormat

FileFormatConfig: TypeAlias = (
    InstanceOf[FileFormat] | Annotated[List[InstanceOf[FileFormat]], MinLen(1)] | None
)

ExporterConfig: TypeAlias = (
    InstanceOf[Exporter]
    | Annotated[List[InstanceOf[Exporter]], MinLen(1)]
    | Annotated[
        Dict[Annotated[AssetType, EnumNameSerializer], InstanceOf[Exporter]], MinLen(1)
    ]
)

TexResConfig: TypeAlias = (
    PositiveInt
    | Annotated[
        Dict[Annotated[BakeType, EnumNameSerializer], PositiveInt],
        MinLen(len(BakeType)),
    ]
)
