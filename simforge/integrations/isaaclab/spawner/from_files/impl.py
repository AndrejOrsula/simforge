from typing import TYPE_CHECKING, Tuple

import omni.isaac.core.utils.prims as prim_utils
import omni.isaac.core.utils.stage as stage_utils
from omni.isaac.lab.sim import clone
from omni.isaac.lab.sim.spawners.from_files.from_files import (
    spawn_from_usd as __spawn_from_usd,
)
from pxr import PhysxSchema, Usd, UsdPhysics  # type: ignore

if TYPE_CHECKING:
    from simforge.integrations.isaaclab.spawner.from_files.cfg import (
        FileCfg,
        UsdFileCfg,
    )


@clone
def spawn_from_usd(
    prim_path: str,
    cfg: "UsdFileCfg",
    translation: Tuple[float, float, float] | None = None,
    orientation: Tuple[float, float, float, float] | None = None,
) -> Usd.Prim:
    # Get prim
    if not prim_utils.is_prim_path_valid(prim_path):
        prim_utils.create_prim(
            prim_path,
            usd_path=cfg.usd_path,
            translation=translation,
            orientation=orientation,
            scale=cfg.scale,
        )
    prim: Usd.Prim = stage_utils.get_current_stage().GetPrimAtPath(prim_path)

    # Apply missing APIs
    __apply_missing_apis(prim, cfg)

    # Apply mesh collision API and properties
    if cfg.mesh_collision_props is not None:
        cfg.mesh_collision_props.func(prim_path, cfg.mesh_collision_props)

    return __spawn_from_usd(prim_path, cfg, translation, orientation)


def __apply_missing_apis(prim: Usd.Prim, cfg: "FileCfg"):
    if cfg.mass_props is not None and not UsdPhysics.MassAPI(prim):  # type: ignore
        UsdPhysics.MassAPI.Apply(prim)  # type: ignore

    if cfg.rigid_props is not None and not UsdPhysics.RigidBodyAPI(prim):  # type: ignore
        UsdPhysics.RigidBodyAPI.Apply(prim)  # type: ignore

    if cfg.collision_props is not None and not UsdPhysics.CollisionAPI(prim):  # type: ignore
        UsdPhysics.CollisionAPI.Apply(prim)  # type: ignore

    if cfg.deformable_props is not None and not PhysxSchema.PhysxDeformableBodyAPI(
        prim
    ):
        PhysxSchema.PhysxDeformableBodyAPI.Apply(prim)

    if cfg.articulation_props is not None and not UsdPhysics.ArticulationRootAPI(prim):  # type: ignore
        UsdPhysics.ArticulationRootAPI.Apply(prim)  # type: ignore

    if cfg.fixed_tendons_props is not None:
        if not PhysxSchema.PhysxTendonAxisAPI(prim):
            PhysxSchema.PhysxTendonAxisAPI.Apply(prim)
        if not PhysxSchema.PhysxTendonAxisRootAPI(prim):
            PhysxSchema.PhysxTendonAxisRootAPI.Apply(prim)

    if cfg.joint_drive_props is not None and not UsdPhysics.DriveAPI(prim):  # type: ignore
        UsdPhysics.DriveAPI.Apply(prim)  # type: ignore
