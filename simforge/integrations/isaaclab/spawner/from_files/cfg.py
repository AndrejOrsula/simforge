from collections.abc import Callable

from isaaclab.sim.spawners import DeformableBodyMaterialCfg, RigidBodyMaterialCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import FileCfg as __FileCfg
from isaaclab.sim.spawners.from_files.from_files_cfg import UsdFileCfg as __UsdFileCfg
from isaaclab.utils import configclass

from simforge.integrations.isaaclab.schemas import MeshCollisionPropertiesCfg
from simforge.integrations.isaaclab.spawner.from_files.impl import spawn_from_usd


@configclass
class FileCfg(__FileCfg):
    mesh_collision_props: MeshCollisionPropertiesCfg | None = None
    physics_material: RigidBodyMaterialCfg | DeformableBodyMaterialCfg | None = None


@configclass
class UsdFileCfg(FileCfg, __UsdFileCfg):
    func: Callable = spawn_from_usd
