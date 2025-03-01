from typing import TYPE_CHECKING

import carb
from isaacsim.core.utils.stage import get_current_stage
from omni.physx.scripts import utils as physx_utils
from pxr import Usd, UsdGeom, UsdPhysics

from pxr import PhysxSchema  # isort: skip

if TYPE_CHECKING:
    from simforge.integrations.isaaclab.schemas.cfg import MeshCollisionPropertiesCfg


def set_mesh_collision_properties(prim_path: str, cfg: "MeshCollisionPropertiesCfg"):
    if cfg.mesh_approximation is None:
        return

    parent_prim: Usd.Prim = get_current_stage().GetPrimAtPath(prim_path)
    _queue = [parent_prim]
    while _queue:
        child_prim = _queue.pop(0)
        _queue.extend(child_prim.GetChildren())

        if not (
            child_prim.IsA(UsdGeom.Mesh) or child_prim.HasAPI(UsdPhysics.CollisionAPI)  # type: ignore
        ):
            continue

        if cfg.mesh_approximation == "none" and __is_part_of_rigid_body(child_prim):
            carb.log_warn(
                f'Prim "{child_prim.GetPath()}" is a part of a rigid body, so its collision mesh should be approximated'
            )

        if not child_prim.HasAPI(PhysxSchema.PhysxCollisionAPI):
            PhysxSchema.PhysxCollisionAPI.Apply(child_prim)
        collision_api = UsdPhysics.CollisionAPI(child_prim)  # type: ignore
        collision_api.CreateCollisionEnabledAttr().Set(True)

        if api := physx_utils.MESH_APPROXIMATIONS.get(cfg.mesh_approximation, None):
            approximation_api = api.Apply(child_prim) if api is not None else None
        if cfg.mesh_approximation == "sdf" and cfg.sdf_resolution:
            approximation_api.CreateSdfResolutionAttr().Set(cfg.sdf_resolution)  # type: ignore

        if not child_prim.HasAPI(UsdPhysics.MeshCollisionAPI):  # type: ignore
            mesh_collision_api = UsdPhysics.MeshCollisionAPI.Apply(child_prim)  # type: ignore
        else:
            mesh_collision_api = UsdPhysics.MeshCollisionAPI(child_prim)  # type: ignore
        mesh_collision_api.CreateApproximationAttr().Set(cfg.mesh_approximation)

    return


def __is_part_of_rigid_body(child_prim: Usd.Prim) -> bool:
    prim = child_prim
    while prim.IsValid():
        if prim.HasAPI(UsdPhysics.RigidBodyAPI):  # type: ignore
            return True
        prim = prim.GetParent()
    return False
