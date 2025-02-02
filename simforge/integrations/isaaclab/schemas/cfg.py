from collections.abc import Callable
from typing import Literal

from isaaclab.utils import configclass

from simforge.integrations.isaaclab.schemas.impl import set_mesh_collision_properties


@configclass
class MeshCollisionPropertiesCfg:
    func: Callable = set_mesh_collision_properties

    mesh_approximation: (
        Literal[
            "none",
            "convexHull",
            "convexDecomposition",
            "meshSimplification",
            "convexMeshSimplification",
            "boundingCube",
            "boundingSphere",
            "sphereFill",
            "sdf",
        ]
        | None
    ) = None
    """Collision approximation to use for the collision shape"""

    sdf_resolution: int = 160
    """Resolution of the SDF grid used for collision approximation"""
