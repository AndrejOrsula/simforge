from __future__ import annotations

from typing import Sequence, Type

from pydantic import InstanceOf, SerializeAsAny

from simforge._typing import TexResConfig
from simforge.core.asset.asset import Asset
from simforge.core.asset.asset_type import AssetType
from simforge.core.asset.geometry import Geometry
from simforge.core.asset.material import Material


class Model(Asset, asset_entrypoint=AssetType.MODEL):
    geo: SerializeAsAny[InstanceOf[Geometry]]
    mat: SerializeAsAny[InstanceOf[Material]] | None = None
    texture_resolution: TexResConfig = 512

    @property
    def requires_baking(self) -> bool:
        return self.mat is not None

    @classmethod
    def registry(cls) -> Sequence[Type[Model]]:
        return super().registry().get(AssetType.MODEL, [])  # type: ignore
