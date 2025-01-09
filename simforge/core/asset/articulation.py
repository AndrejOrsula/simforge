from __future__ import annotations

from typing import Sequence, Type

from simforge.core.asset.asset import Asset, AssetRegistry
from simforge.core.asset.asset_type import AssetType


class Articulation(Asset, asset_entrypoint=AssetType.ARTICULATION):
    @classmethod
    def registry(cls) -> Sequence[Type[Articulation]]:
        return AssetRegistry.registry.get(AssetType.ARTICULATION, [])  # type: ignore
