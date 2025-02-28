from typing import TYPE_CHECKING, Tuple

import isaacsim.core.utils.prims as prim_utils
import isaacsim.core.utils.stage as stage_utils
from isaaclab.sim import clone
from isaaclab.sim.spawners.from_files.from_files import (
    spawn_from_usd as __spawn_from_usd,
)
from pxr import PhysxSchema, Usd, UsdGeom, UsdPhysics

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

    # Apply missing APIs
    __apply_missing_apis(prim_path, cfg)

    # Apply mesh collision API and properties
    if cfg.mesh_collision_props is not None:
        cfg.mesh_collision_props.func(prim_path, cfg.mesh_collision_props)

    return __spawn_from_usd(prim_path, cfg, translation, orientation)


def __apply_missing_apis(prim_path: str, cfg: "FileCfg"):
    parent_prim: Usd.Prim = stage_utils.get_current_stage().GetPrimAtPath(prim_path)

    if cfg.articulation_props is not None:
        articulation_root_prim: Usd.Prim | None = None
        _queue = [parent_prim]
        while _queue:
            child_prim = _queue.pop(0)
            if child_prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                articulation_root_prim = child_prim
                break
            _queue.extend(child_prim.GetChildren())
        if articulation_root_prim is None:
            UsdPhysics.ArticulationRootAPI.Apply(parent_prim)

    if cfg.fixed_tendons_props is not None:
        fixed_tendon_root_prim: Usd.Prim | None = None
        _queue = [parent_prim]
        while _queue:
            child_prim = _queue.pop(0)
            if child_prim.HasAPI(PhysxSchema.PhysxTendonAxisRootAPI):
                fixed_tendon_root_prim = child_prim
                break
            _queue.extend(child_prim.GetChildren())
        if fixed_tendon_root_prim is None:
            PhysxSchema.PhysxTendonAxisRootAPI.Apply(parent_prim)

    for child_prim in parent_prim.GetChildren():
        if (
            child_prim.IsA(UsdGeom.Xform)
            or child_prim.IsA(UsdGeom.Mesh)
            or child_prim.IsA(UsdGeom.Gprim)
        ):
            if cfg.collision_props is not None and not child_prim.HasAPI(
                UsdPhysics.CollisionAPI
            ):
                UsdPhysics.CollisionAPI.Apply(child_prim)

            if cfg.rigid_props is not None and not child_prim.HasAPI(
                UsdPhysics.RigidBodyAPI
            ):
                UsdPhysics.RigidBodyAPI.Apply(child_prim)

            if cfg.mass_props is not None and not child_prim.HasAPI(UsdPhysics.MassAPI):
                UsdPhysics.MassAPI.Apply(child_prim)

            if cfg.deformable_props is not None and not child_prim.HasAPI(
                PhysxSchema.PhysxDeformableBodyAPI
            ):
                PhysxSchema.PhysxDeformableBodyAPI.Apply(child_prim)
        elif child_prim.IsA(UsdPhysics.Joint) and not child_prim.IsA(
            UsdPhysics.FixedJoint
        ):
            if cfg.joint_drive_props is not None and not child_prim.HasAPI(
                UsdPhysics.DriveAPI
            ):
                UsdPhysics.DriveAPI.Apply(child_prim)
