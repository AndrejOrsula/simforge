from typing import TYPE_CHECKING, Any, Tuple

import isaacsim.core.utils.prims as prim_utils
import isaacsim.core.utils.stage as stage_utils
from isaaclab.sim import clone
from isaaclab.sim.spawners.from_files.from_files import (
    spawn_from_usd as __spawn_from_usd,
)
from pxr import Usd, UsdGeom, UsdPhysics

from pxr import PhysxSchema  # isort: skip

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
    **kwargs,
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
    _apply_missing_apis(prim_path, cfg)

    # Apply mesh collision API and properties
    if cfg.mesh_collision_props is not None:
        cfg.mesh_collision_props.func(prim_path, cfg.mesh_collision_props)

    return __spawn_from_usd(prim_path, cfg, translation, orientation, **kwargs)


def _apply_missing_apis(prim_path: str, cfg: "FileCfg"):
    parent_prim: Usd.Prim = stage_utils.get_current_stage().GetPrimAtPath(prim_path)

    if cfg.articulation_props is not None and not __has_child_with_api(
        parent_prim,
        UsdPhysics.ArticulationRootAPI,  # type: ignore
    ):
        UsdPhysics.ArticulationRootAPI.Apply(parent_prim)  # type: ignore

    queue = parent_prim.GetChildren()
    while queue:
        child_prim = queue.pop(0)
        queue.extend(child_prim.GetChildren())

        if (
            cfg.joint_drive_props is not None
            and (
                child_prim.IsA(UsdPhysics.Joint)  # type: ignore
                and not child_prim.IsA(UsdPhysics.FixedJoint)  # type: ignore
            )
            and not child_prim.HasAPI(UsdPhysics.DriveAPI)  # type: ignore
        ):
            UsdPhysics.DriveAPI.Apply(child_prim, f"{child_prim.GetName()}_drive")  # type: ignore

        else:
            if child_prim.IsA(UsdGeom.Xform) and (
                cfg.rigid_props is not None
                and not __has_child_with_api(
                    child_prim,
                    UsdPhysics.RigidBodyAPI,  # type: ignore
                )
                and not __has_parent_with_api(
                    child_prim,
                    UsdPhysics.RigidBodyAPI,  # type: ignore
                )
            ):
                UsdPhysics.RigidBodyAPI.Apply(child_prim)  # type: ignore

            if child_prim.IsA(UsdGeom.Xformable) and (
                cfg.mass_props is not None
                and __has_parent_with_api(
                    child_prim,
                    UsdPhysics.RigidBodyAPI,  # type: ignore
                )
                and not __has_child_with_api_or_instance(
                    child_prim,
                    UsdPhysics.MassAPI,  # type: ignore
                )
                and not __has_parent_with_api(
                    child_prim,
                    UsdPhysics.MassAPI,  # type: ignore
                )
            ):
                UsdPhysics.MassAPI.Apply(child_prim)  # type: ignore

            if child_prim.IsA(UsdGeom.Gprim):
                if (
                    cfg.collision_props is not None
                    and not __has_child_with_api_or_instance(
                        child_prim,
                        UsdPhysics.CollisionAPI,  # type: ignore
                    )
                    and not __has_parent_with_api(
                        child_prim,
                        UsdPhysics.CollisionAPI,  # type: ignore
                    )
                ):
                    UsdPhysics.CollisionAPI.Apply(child_prim)  # type: ignore

                if (
                    cfg.deformable_props is not None
                    and not __has_child_with_api_or_instance(
                        child_prim,
                        PhysxSchema.PhysxDeformableBodyAPI,  # type: ignore
                    )
                    and not __has_parent_with_api(
                        child_prim,
                        PhysxSchema.PhysxDeformableBodyAPI,  # type: ignore
                    )
                ):
                    PhysxSchema.PhysxDeformableBodyAPI.Apply(child_prim)  # type: ignore


def __has_parent_with_api(child_prim: Usd.Prim, api_schema: Any) -> bool:
    prim = child_prim
    while prim.IsValid():
        if prim.HasAPI(api_schema):
            return True
        prim = prim.GetParent()
    return False


def __has_child_with_api(parent_prim: Usd.Prim, api_schema: Any) -> bool:
    queue = [parent_prim]
    while queue:
        child_prim = queue.pop(0)
        if child_prim.HasAPI(api_schema):
            return True
        queue.extend(child_prim.GetChildren())
    return False


def __has_child_with_api_or_instance(parent_prim: Usd.Prim, api_schema: Any) -> bool:
    queue = [parent_prim]
    while queue:
        child_prim = queue.pop(0)
        if child_prim.IsInstance() or child_prim.HasAPI(api_schema):
            return True
        queue.extend(child_prim.GetChildren())
    return False
