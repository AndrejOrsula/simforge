from collections.abc import Callable
from dataclasses import MISSING
from typing import Any, List, Mapping

from isaaclab.utils import configclass

from simforge import Articulation, Geometry, Model
from simforge.integrations.isaaclab.spawner.from_files import FileCfg
from simforge.integrations.isaaclab.spawner.simforge_asset.impl import (
    spawn_simforge_assets,
)


@configclass
class SimforgeAssetCfg(FileCfg):
    func: Callable = spawn_simforge_assets

    assets: List[Articulation | Geometry | Model] = MISSING  # type: ignore
    export_kwargs: Mapping[str, Any] = {}

    num_assets: int = 1
    seed: int = 0
    use_cache: bool = True

    random_choice: bool = False
