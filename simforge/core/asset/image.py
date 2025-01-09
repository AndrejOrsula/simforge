from __future__ import annotations

from typing import Sequence, Type

from simforge.core.asset.asset import Asset, AssetRegistry
from simforge.core.asset.asset_type import AssetType


class Image(Asset, asset_entrypoint=AssetType.IMAGE):
    @classmethod
    def registry(cls) -> Sequence[Type[Image]]:
        return AssetRegistry.registry.get(AssetType.IMAGE, [])  # type: ignore
