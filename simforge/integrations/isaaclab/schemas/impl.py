from typing import TYPE_CHECKING

import carb
import omni.isaac.core.utils.stage as stage_utils
from omni.isaac.lab.sim import apply_nested
from omni.physx.scripts import utils as physx_utils
from pxr import PhysxSchema, Usd, UsdPhysics

if TYPE_CHECKING:
    from simforge.integrations.isaaclab.schemas.cfg import MeshCollisionPropertiesCfg


@apply_nested
def set_mesh_collision_properties(
    prim_path: str,
    cfg: "MeshCollisionPropertiesCfg",
) -> bool:
    """

    Args:
        prim_path: The prim path of parent.
        cfg: The configuration for the collider.

    Returns:
        True if the properties were successfully set, False otherwise.
    """

    # Apply mesh collision approximation
    if cfg.mesh_approximation is not None:
        prim: Usd.Prim = stage_utils.get_current_stage().GetPrimAtPath(prim_path)

        if physx_utils.hasSchema(prim, "CollisionAPI"):
            carb.log_warn("CollisionAPI is already defined")
            return False

        def isPartOfRigidBody(currPrim):
            if currPrim.HasAPI(UsdPhysics.RigidBodyAPI):  # type: ignore
                return True

            currPrim = currPrim.GetParent()

            return isPartOfRigidBody(currPrim) if currPrim.IsValid() else False

        if cfg.mesh_approximation == "none" and isPartOfRigidBody(prim):
            carb.log_warn(
                f"setCollider: {prim.GetPath()} is a part of a rigid body. Resetting approximation shape from none (trimesh) to convexHull"
            )
            cfg.mesh_approximation = "convexHull"

        collisionAPI = UsdPhysics.CollisionAPI.Apply(prim)  # type: ignore
        PhysxSchema.PhysxCollisionAPI.Apply(prim)
        collisionAPI.CreateCollisionEnabledAttr().Set(True)

        api = physx_utils.MESH_APPROXIMATIONS.get(
            cfg.mesh_approximation, 0
        )  # None is a valid value
        if api == 0:
            carb.log_warn(
                f"setCollider: invalid approximation type {cfg.mesh_approximation} provided for {prim.GetPath()}. Falling back to convexHull."
            )
            cfg.mesh_approximation = "convexHull"
            api = physx_utils.MESH_APPROXIMATIONS[cfg.mesh_approximation]
        approximation_api = api.Apply(prim) if api is not None else None
        if cfg.mesh_approximation == "sdf" and cfg.sdf_resolution:
            approximation_api.CreateSdfResolutionAttr().Set(cfg.sdf_resolution)  # type: ignore

        meshcollisionAPI = UsdPhysics.MeshCollisionAPI.Apply(prim)  # type: ignore
        meshcollisionAPI.CreateApproximationAttr().Set(cfg.mesh_approximation)

    return True
