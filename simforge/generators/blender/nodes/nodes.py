from functools import cached_property
from typing import TYPE_CHECKING, Dict, List, Mapping, Sequence

from pydantic import BaseModel, Field

from simforge.utils import canonicalize_str

COMMON_INPUT_ALIASES: Dict[str, List[str]] = {
    "seed": [
        "pseodorandomseed",
        "randomseed",
        "rng",
    ],
    "detail": [
        "detaillevel",
        "detailobject",
        "levelofdetail",
        "subdivisionlevel",
        "subdivisions",
        "subdivlevel",
    ],
    "size": [
        "dimensions",
    ],
    "scale": [
        "scaling",
    ],
    "mat": [
        "material",
    ],
}

if TYPE_CHECKING:
    import bpy


class BlNodes(BaseModel, defer_build=True):
    name: str = Field(frozen=True)

    @cached_property
    def is_randomizable(self) -> bool:
        return "seed" in self.input_mapping.keys()

    @property
    def group(
        self,
    ) -> "bpy.types.NodeTree | bpy.types.CompositorNodeTree | bpy.types.ShaderNodeTree | bpy.types.GeometryNodeTree | bpy.types.TextureNodeTree":
        import bpy

        return bpy.data.node_groups[self.name]

    @cached_property
    def input_mapping(self) -> Mapping[str, str]:
        import bpy

        # Get the node group
        node_group = bpy.data.node_groups[self.name]

        # Extract a map of the input socket mapping
        input_mapping = {
            canonicalize_str(item.name): (item.identifier)  # type: ignore
            for item in node_group.interface.items_tree.values()
            if item.item_type == "SOCKET" and item.in_out == "INPUT"  # type: ignore
        }

        # Rename common aliases for convenience
        for target, possible_alias in COMMON_INPUT_ALIASES.items():
            original_alias: str | None = (
                target if target in input_mapping.keys() else None
            )
            for key in input_mapping.keys():
                if key in possible_alias:
                    if original_alias is not None:
                        raise ValueError(
                            f'Ambiguous name of the input socket "{target}" (canonicalized): "{original_alias}", "{key}"'
                        )
                    original_alias = key
            if original_alias is not None and original_alias != target:
                input_mapping[target] = input_mapping[original_alias]

        return input_mapping

    @cached_property
    def material_input_names(self) -> Sequence[str]:
        import bpy

        return [
            canonicalize_str(item.name)  # type: ignore
            for item in bpy.data.node_groups[self.name].interface.items_tree.values()
            if item.item_type == "SOCKET"  # type: ignore
            and item.in_out == "INPUT"  # type: ignore
            and item.socket_type == "NodeSocketMaterial"  # type: ignore
        ]
