from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Mapping, Sequence, Tuple

import simforge
from simforge import Asset, Generator, ModelFileFormat
from simforge._typing import ExporterConfig
from simforge.generators.blender.baker import BlBaker
from simforge.generators.blender.exporter import BlModelExporter
from simforge.generators.blender.version import verify_bpy_version

if TYPE_CHECKING:
    import bpy

    from simforge.generators.blender.asset import BlGeometry, BlModel


class BlGenerator(Generator):
    EXPORTERS: ClassVar[ExporterConfig] = BlModelExporter()
    BAKER: ClassVar[BlBaker] = BlBaker()
    SUBPROC_PYTHON_EXPR: ClassVar[Sequence[str]] = [
        Path(simforge.__file__)
        .parent.joinpath("scripts")
        .joinpath("blender")
        .joinpath("python_expr.bash")
        .as_posix()
    ]

    ALWAYS_REALIZE_INSTANCES: ClassVar[bool] = True

    def generate(
        self, asset: Asset, export_kwargs: Mapping[str, Any] = {}, **kwargs
    ) -> Sequence[Tuple[Path, Mapping[str, Any]]]:
        import bpy

        verify_bpy_version()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        return super().generate(asset, export_kwargs, **kwargs)

    @cached_property
    def _should_realize_instances(self) -> bool:
        return self.ALWAYS_REALIZE_INSTANCES or any(
            exporter.file_format
            not in (
                ModelFileFormat.ABC,
                ModelFileFormat.USD,
                ModelFileFormat.USDA,
                ModelFileFormat.USDC,
                ModelFileFormat.USDZ,
            )
            for exporter in self.exporters.values()
            if isinstance(exporter.file_format, ModelFileFormat)
        )

    @staticmethod
    def __setup_realize_instances(
        modifier: "bpy.types.Modifier | bpy.types.NodesModifier",
    ):
        import bpy

        if modifier.type != "NODES":
            return

        node_group: bpy.types.GeometryNodeTree = modifier.node_group  # type: ignore
        output_node = node_group.nodes["Group Output"]
        current_link = output_node.inputs[0].links[0]  # type: ignore
        added_node = node_group.nodes.new(type="GeometryNodeRealizeInstances")
        from_socket = current_link.from_socket
        node_group.links.remove(current_link)
        node_group.links.new(added_node.inputs[0], from_socket)
        node_group.links.new(output_node.inputs[0], added_node.outputs[0])

    @staticmethod
    def __reverse_realize_instances(
        modifier: "bpy.types.Modifier | bpy.types.NodesModifier",
    ):
        import bpy

        if modifier.type != "NODES":
            return

        node_group: bpy.types.GeometryNodeTree = modifier.node_group  # type: ignore
        output_node = node_group.nodes["Group Output"]
        current_link = output_node.inputs[0].links[0]  # type: ignore
        added_node = current_link.from_node
        preceding_link = added_node.inputs[0].links[0]  # type: ignore
        from_socket = preceding_link.from_socket
        node_group.links.remove(preceding_link)
        node_group.links.remove(current_link)
        node_group.nodes.remove(added_node)
        node_group.links.new(output_node.inputs[0], from_socket)

    # Geometry

    def _setup_geometry(
        self,
        asset: "BlGeometry",
        **kwargs,
    ) -> Dict[str, Any]:
        # Create prototype asset
        asset.setup()

        # If required, realize instances for all node-based modifiers
        if self._should_realize_instances:
            for modifier in asset.obj.modifiers:
                self.__setup_realize_instances(modifier)

        return kwargs

    def _generate_geometry(
        self,
        asset: "BlGeometry",
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        import bpy

        # Duplicate the prototype asset
        duplicate_geom = asset.duplicate(name=f"{{NAME}}{seed}")

        # Seed the duplicated asset
        duplicate_geom.seed(seed)

        # Apply all modifiers on the duplicated asset
        for modifier in duplicate_geom.obj.modifiers:
            bpy.ops.object.modifier_apply(modifier=modifier.name)

        generate_kwargs = setup_kwargs
        generate_kwargs["duplicate_geom"] = duplicate_geom
        return generate_kwargs

    def _export_geometry(
        self,
        asset: "BlGeometry",
        seed: int,
        duplicate_geom: "BlGeometry",
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        import bpy

        filepath, _ = super()._export_geometry(
            asset, seed=seed, export_kwargs=export_kwargs
        )

        # Cleanup the duplicated asset
        duplicate_geom.cleanup()
        # Purge orphaned data
        bpy.data.orphans_purge()

        metadata = generate_kwargs
        return filepath, metadata

    def _cleanup_geometry(
        self,
        asset: "BlGeometry",
    ):
        import bpy

        # Reverse the realization of instances for all node-based modifiers
        if self._should_realize_instances:
            for modifier in asset.obj.modifiers:
                if modifier is None:
                    continue
                self.__reverse_realize_instances(modifier)

        # Cleanup the prototype asset
        asset.cleanup()
        # Purge orphaned data
        bpy.data.orphans_purge()

    # Model

    def _setup_model(
        self,
        asset: "BlModel",
        **kwargs,
    ) -> Dict[str, Any]:
        # Create prototype asset
        asset.setup()

        # If required, realize instances for all node-based modifiers
        if self._should_realize_instances:
            for modifier in asset.geo.obj.modifiers:
                self.__setup_realize_instances(modifier)

        setup_kwargs = kwargs
        return setup_kwargs

    def _generate_model(
        self,
        asset: "BlModel",
        seed: int,
        **setup_kwargs,
    ) -> Dict[str, Any]:
        import bpy

        # Duplicate the prototype asset
        duplicate_geom = asset.geo.duplicate(name=f"{{NAME}}{seed}")

        # Seed the duplicated asset
        duplicate_geom.seed(seed)

        # Apply all modifiers on the duplicated asset
        for modifier in duplicate_geom.obj.modifiers:
            if modifier is None:
                continue
            bpy.ops.object.modifier_apply(modifier=modifier.name)

        # Assign material to the duplicated asset
        if material := asset.mat:
            duplicate_geom.mesh.materials.clear()
            duplicate_geom.mesh.materials.append(material.mat)

        # Bake the material into textures
        if asset.requires_baking and self.model_exporter_supports_material:
            self.BAKER.bake(asset.texture_resolution)

        generate_kwargs = setup_kwargs
        generate_kwargs["duplicate_geom"] = duplicate_geom
        return generate_kwargs

    def _export_model(
        self,
        asset: "BlModel",
        seed: int,
        duplicate_geom: "BlGeometry",
        export_kwargs: Mapping[str, Any] = {},
        **generate_kwargs,
    ) -> Tuple[Path, Dict[str, Any]]:
        import bpy

        filepath, _ = super()._export_model(
            asset, seed=seed, export_kwargs=export_kwargs
        )

        # Cleanup the duplicated asset
        duplicate_geom.cleanup()

        # Remove the baked textures
        # Bake the material into textures
        if asset.requires_baking and self.model_exporter_supports_material:
            self.BAKER.cleanup()

        # Purge orphaned data
        bpy.data.orphans_purge()

        metadata = generate_kwargs
        return filepath, metadata

    def _cleanup_model(
        self,
        asset: "BlModel",
    ):
        import bpy

        # Reverse the realization of instances for all node-based modifiers
        if self._should_realize_instances:
            for modifier in asset.geo.obj.modifiers:
                if modifier is None:
                    continue
                self.__reverse_realize_instances(modifier)

        # Cleanup the prototype asset
        asset.cleanup()
        # Purge orphaned data
        bpy.data.orphans_purge()
