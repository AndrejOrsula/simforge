from __future__ import annotations

from typing import Sequence, Type

from simforge.core.asset.asset import Asset, AssetRegistry
from simforge.core.asset.asset_type import AssetType


class Material(Asset, asset_entrypoint=AssetType.MATERIAL):
    @classmethod
    def registry(cls) -> Sequence[Type[Material]]:
        return AssetRegistry.registry.get(AssetType.MATERIAL, [])  # type: ignore
