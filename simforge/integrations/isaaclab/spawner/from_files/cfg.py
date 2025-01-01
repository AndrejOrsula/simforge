from collections.abc import Callable

from omni.isaac.lab.sim.spawners.from_files.from_files_cfg import FileCfg as __FileCfg
from omni.isaac.lab.sim.spawners.from_files.from_files_cfg import (
    UsdFileCfg as __UsdFileCfg,
)
from omni.isaac.lab.utils import configclass

from simforge.integrations.isaaclab.schemas import MeshCollisionPropertiesCfg
from simforge.integrations.isaaclab.spawner.from_files.impl import spawn_from_usd


@configclass
class FileCfg(__FileCfg):
    mesh_collision_props: MeshCollisionPropertiesCfg | None = None


@configclass
class UsdFileCfg(FileCfg, __UsdFileCfg):
    func: Callable = spawn_from_usd
