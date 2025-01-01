from __future__ import annotations

from typing import Sequence, Type

from simforge.core.asset.asset import Asset
from simforge.core.asset.asset_type import AssetType


class Material(Asset, asset_entrypoint=AssetType.MATERIAL):
    @classmethod
    def registry(cls) -> Sequence[Type[Material]]:
        return super().registry().get(AssetType.MATERIAL, [])  # type: ignore
