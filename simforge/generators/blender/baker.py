import contextlib
import io
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Dict, Iterable, Tuple

from annotated_types import MinLen
from pydantic import PositiveFloat, PositiveInt

from simforge import Baker, BakeType
from simforge._typing import EnumNameSerializer
from simforge.utils import suppress_stdout

if TYPE_CHECKING:
    import bpy


class BlBaker(Baker):
    render_samples: (
        PositiveInt
        | Annotated[
            Dict[Annotated[BakeType, EnumNameSerializer], PositiveInt], MinLen(1)
        ]
    ) = {
        BakeType.ALBEDO: 3,
        BakeType.NORMAL: 4,
        BakeType.ROUGHNESS: 2,
        BakeType.METALLIC: 1,
        BakeType.EMISSION: 1,
    }
    uv_angle_limit: PositiveFloat = 0.785398

    _baked_textures: ClassVar[Dict[BakeType, "bpy.types.Image"]] = {}

    def setup(self):
        import bpy

        if not self.enabled:
            return

        # Configure Cycles for GPU rendering
        context: bpy.types.Context = bpy.context  # type: ignore
        cycles_preferences = context.preferences.addons["cycles"].preferences
        cycles_preferences.compute_device_type = "CUDA"  # type: ignore
        cycles_preferences.get_devices()  # type: ignore
        for device in cycles_preferences.devices:  # type: ignore
            device.use = device.type == "CUDA"

        # Set the render engine to Cycles
        scene: bpy.types.Scene = context.scene
        scene.cycles.device = "GPU"
        scene.render.engine = "CYCLES"  # type: ignore

    def bake(self, texture_resolution: int | Dict[BakeType, int]):
        import bpy

        if not self.enabled:
            return

        # Standardize the texture resolution input
        if isinstance(texture_resolution, int):
            assert texture_resolution > 0, "Texture resolution must be positive"
            texture_resolution = {
                bake_type: texture_resolution for bake_type in BakeType
            }

        scene: bpy.types.Scene = bpy.context.scene  # type: ignore

        # Prepare a list of objects and materials to bake
        objects_to_bake = [
            obj
            for obj in bpy.data.objects
            if obj.select_get()
            and not obj.hide_render
            and isinstance(obj.data, bpy.types.Mesh)
            and obj.data.materials
        ]
        if not objects_to_bake:
            return
        for obj in objects_to_bake:
            for index, slot in reversed(list(enumerate(obj.material_slots))):
                mat = slot.material
                if mat is None or not mat.use_nodes:
                    bpy.context.object.active_material_index = index  # type: ignore
                    bpy.ops.object.material_slot_remove()
        materials_to_bake = {
            mat
            for obj in objects_to_bake
            for mat in obj.data.materials  # type: ignore
            if mat is not None and mat.use_nodes
        }
        if not materials_to_bake:
            return

        # Unwrap UVs
        self._unwrap_selected(objects_to_bake, min(texture_resolution.values()))

        # Get scalar inputs of the shader nodes
        shader_const_inputs = self._get_shader_const_inputs(materials_to_bake)

        # Bake each texture type
        material_name = f"mat_{objects_to_bake[0].name}"
        for bake_type in BakeType:
            # Skip if the corresponding input socket is set to a constant scalar
            match bake_type:
                case BakeType.EMISSION:
                    emission_strength_input = shader_const_inputs.get(
                        "Emission Strength", (None, 1.0)
                    )[1]
                    emission_color_input = shader_const_inputs.get(
                        "Emission Color", (None, (1.0, 1.0, 1.0, 1.0))
                    )[1]
                    if (
                        emission_strength_input <= 0.0
                        or emission_color_input[:3] == (0.0, 0.0, 0.0)
                        or emission_color_input[3] == 0.0
                    ):
                        continue
                case _:
                    if (
                        self._shader_input_socket_name_from_type(bake_type)
                        in shader_const_inputs.keys()
                    ):
                        continue

            if bake_type not in texture_resolution.keys():
                raise ValueError(
                    f'Missing texture resolution for bake type "{bake_type.name}"'
                )

            # Update bake settings
            scene.cycles.samples = (
                self.render_samples
                if isinstance(self.render_samples, int)
                else self.render_samples.get(bake_type, 1)
            )
            scene.render.bake.margin = max(1, texture_resolution[bake_type] // 128)

            # Bake the texture
            self._baked_textures[bake_type] = self._bake_single_pass(
                bake_type=bake_type,
                materials_to_bake=materials_to_bake,
                texture_resolution=texture_resolution[bake_type],
                texture_basename=material_name,
            )

        # Create a new material from the baked textures
        baked_material = self._setup_baked_material(
            name=material_name,
            baked_textures=self._baked_textures,
            shader_const_inputs=shader_const_inputs,
        )

        # Replace the original materials with the new material
        for obj in objects_to_bake:
            mesh: bpy.types.Mesh = obj.data  # type: ignore
            mesh.materials.clear()
            mesh.materials.append(baked_material)

    def cleanup(self):
        import bpy

        if not self.enabled:
            return

        for texture in self._baked_textures.values():
            bpy.data.images.remove(texture)
        self._baked_textures.clear()

    @classmethod
    def _bake_single_pass(
        cls,
        bake_type: BakeType,
        materials_to_bake: Iterable["bpy.types.Material"],
        texture_resolution: int,
        texture_basename: str,
    ) -> "bpy.types.Image":
        import bpy

        match bake_type:
            case BakeType.ALBEDO:
                changes: Dict[int, Dict[str, Any]] = {}
                for i, mat in enumerate(materials_to_bake):
                    node_tree: bpy.types.ShaderNodeTree = mat.node_tree  # type: ignore
                    shader_res = cls._find_shader(node_tree)
                    if shader_res is None:
                        continue
                    shader, shader_group_tree = shader_res

                    # Get undesired sockets
                    metallic_socket = shader.inputs["Metallic"]
                    sheen_weight_socket = shader.inputs["Sheen Weight"]
                    clearcoat_weight_socket = shader.inputs["Coat Weight"]

                    changes[i] = {
                        "node_tree": shader_group_tree,
                        "metallic_socket": metallic_socket,
                        "metallic_default": metallic_socket.default_value,  # type: ignore
                        "sheen_weight_socket": sheen_weight_socket,
                        "sheen_weight_default": sheen_weight_socket.default_value,  # type: ignore
                        "clearcoat_weight_socket": clearcoat_weight_socket,
                        "clearcoat_weight_default": clearcoat_weight_socket.default_value,  # type: ignore
                    }

                    # Temporarily disconnect any metallic link
                    if metallic_socket.is_linked:
                        metallic_socket_link = metallic_socket.links[0]  # type: ignore
                        changes[i]["metallic_from_socket"] = (
                            metallic_socket_link.from_socket
                        )
                        shader_group_tree.links.remove(metallic_socket_link)

                    # Temporarily set the default values to 0.0
                    metallic_socket.default_value = 0.0  # type: ignore
                    sheen_weight_socket.default_value = 0.0  # type: ignore
                    clearcoat_weight_socket.default_value = 0.0  # type: ignore

                texture = cls.__bake_single_pass_inner(
                    bake_type=bake_type,
                    materials_to_bake=materials_to_bake,
                    texture_resolution=texture_resolution,
                    texture_basename=texture_basename,
                )

                for i, mat in enumerate(materials_to_bake):
                    if changes_i := changes.get(i):
                        shader_group_tree = changes_i["node_tree"]
                        metallic_socket = changes_i["metallic_socket"]
                        metallic_socket.default_value = changes_i["metallic_default"]
                        changes_i["sheen_weight_socket"].default_value = changes_i[
                            "sheen_weight_default"
                        ]
                        changes_i["clearcoat_weight_socket"].default_value = changes_i[
                            "clearcoat_weight_default"
                        ]
                        if from_socket := changes_i.get("metallic_from_socket"):
                            shader_group_tree.links.new(metallic_socket, from_socket)

                return texture

            case BakeType.METALLIC:
                changes: Dict[int, Dict[str, Any]] = {}
                for i, mat in enumerate(materials_to_bake):
                    node_tree: bpy.types.ShaderNodeTree = mat.node_tree  # type: ignore
                    shader_res = cls._find_shader(node_tree)
                    if shader_res is None:
                        continue
                    shader, shader_group_tree = shader_res

                    # Find the input socket of the output shader in the group of the shader node
                    group_output_node = next(
                        node
                        for node in shader_group_tree.nodes
                        if isinstance(node, bpy.types.NodeGroupOutput)
                    )
                    group_output_node_shader_input_socket = next(
                        input
                        for input in group_output_node.inputs
                        if input.type == "SHADER"
                    )
                    assert (
                        group_output_node_shader_input_socket.is_linked
                    ), "The input socket of a shader node group output must be linked"
                    group_output_node_shader_link = (
                        group_output_node_shader_input_socket.links[0]  # type: ignore
                    )

                    # Get the metallic socket
                    metallic_socket = shader.inputs["Metallic"]

                    changes[i] = {
                        "node_tree": shader_group_tree,
                        "socket": group_output_node_shader_input_socket,
                        "from_socket": group_output_node_shader_link.from_socket,
                    }

                    # Temporarily disconnect the link to the shader node group output
                    shader_group_tree.links.remove(group_output_node_shader_link)

                    if metallic_socket.is_linked:
                        # If metallic input is linked, use the same connection for the shader node group output
                        changes[i]["new_link"] = shader_group_tree.links.new(
                            group_output_node_shader_input_socket,
                            metallic_socket.links[0].from_socket,  # type: ignore
                        )
                    else:
                        # Otherwise, create an RGB node with the original default value and connect it to the shader node group output
                        rgb_node: bpy.types.ShaderNodeRGB = shader_group_tree.nodes.new(
                            type="ShaderNodeRGB"
                        )  # type: ignore
                        rgb_node.outputs[0].default_value = (  # type: ignore
                            *((metallic_socket.default_value,) * 3),  # type: ignore
                            1.0,
                        )
                        new_link = shader_group_tree.links.new(
                            group_output_node_shader_input_socket,
                            rgb_node.outputs[0],
                        )
                        changes[i].update(
                            {
                                "rgb_node": rgb_node,
                                "new_link": new_link,
                            }
                        )

                texture = cls.__bake_single_pass_inner(
                    bake_type=bake_type,
                    materials_to_bake=materials_to_bake,
                    texture_resolution=texture_resolution,
                    texture_basename=texture_basename,
                )

                for i, mat in enumerate(materials_to_bake):
                    if changes_i := changes.get(i):
                        shader_group_tree = changes_i["node_tree"]
                        shader_group_tree.links.remove(changes_i["new_link"])
                        if node := changes_i.get("rgb_node"):
                            shader_group_tree.nodes.remove(node)
                        shader_group_tree.links.new(
                            changes_i["socket"],
                            changes_i["from_socket"],
                        )

                return texture

            case _:
                return cls.__bake_single_pass_inner(
                    bake_type=bake_type,
                    materials_to_bake=materials_to_bake,
                    texture_resolution=texture_resolution,
                    texture_basename=texture_basename,
                )

    @classmethod
    @suppress_stdout
    def __bake_single_pass_inner(
        cls,
        bake_type: BakeType,
        materials_to_bake: Iterable["bpy.types.Material"],
        texture_resolution: int,
        texture_basename: str,
    ) -> "bpy.types.Image":
        import bpy

        texture_name = f"{texture_basename}_{bake_type.name.lower()}"
        image_node_name = f"TexImage_{texture_name}"

        # Create a new image texture into which the bake will be rendered
        texture = bpy.data.images.new(
            name=f"{texture_basename}_{bake_type.name.lower()}",
            width=texture_resolution,
            height=texture_resolution,
            alpha=False,
            float_buffer=False,
            tiled=False,
            is_data=bake_type != BakeType.ALBEDO,
        )

        # Setup materials: Create a new texture node that the bake will target
        for mat in materials_to_bake:
            node_tree: bpy.types.NodeTree = mat.node_tree  # type: ignore
            image_node: bpy.types.TextureNodeImage = node_tree.nodes.new(
                "ShaderNodeTexImage"
            )  # type: ignore
            image_node.name = image_node_name
            image_node.image = texture
            node_tree.nodes.active = image_node
            image_node.select = True

        # Bake
        bpy.ops.object.bake(
            type=cls._bake_pass_from_type(bake_type), pass_filter={"COLOR"}
        )

        # Cleanup materials: Remove the added texture node
        for mat in materials_to_bake:
            node_tree: bpy.types.NodeTree = mat.node_tree  # type: ignore
            image_node: bpy.types.TextureNodeImage = node_tree.nodes.get(
                image_node_name
            )  # type: ignore
            node_tree.nodes.remove(image_node)

        return texture

    def _unwrap_selected(
        self, objects: Iterable["bpy.types.Object"], lowest_resolution: int
    ):
        import bpy

        # Ensure all objects have a UV map
        for obj in objects:
            mesh: bpy.types.Mesh = obj.data  # type: ignore
            if not mesh.uv_layers:
                mesh.uv_layers.new(name="uv")
                mesh.uv_layers["uv"].active = True

        # Go to edit mode and select all vertices
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")

        # Try with the default unwrap first, but capture the output in case it fails (printed as warning to stdout)
        stdout_str = io.StringIO()
        with contextlib.redirect_stdout(stdout_str):
            bpy.ops.uv.unwrap(method="MINIMUM_STRETCH")
        if "failed" in stdout_str.getvalue():
            # If the default unwrap fails, try the smart project unwrap
            bpy.ops.uv.smart_project(
                angle_limit=self.uv_angle_limit,
                island_margin=0.125 / lowest_resolution,
                rotate_method="AXIS_ALIGNED",
                margin_method="ADD",
                scale_to_bounds=True,
            )

        # Return to object mode
        bpy.ops.object.mode_set(mode="OBJECT")

    @classmethod
    def _get_shader_const_inputs(
        cls,
        materials_to_bake: Iterable["bpy.types.Material"],
    ) -> Dict[str, Tuple[int, Any]]:
        import bpy

        default_values = {}

        for mat in materials_to_bake:
            node_tree: bpy.types.ShaderNodeTree = mat.node_tree  # type: ignore
            shader_res = cls._find_shader(node_tree)
            if shader_res is None:
                continue
            shader, _ = shader_res

            for i, input_socket in enumerate(shader.inputs):
                if input_socket.name == "Emission Strength":
                    emission_color_input = shader.inputs["Emission Color"]
                    if not emission_color_input.is_linked and (
                        emission_color_input.default_value[:3] == (0.0, 0.0, 0.0)  # type: ignore
                        or emission_color_input.default_value[3] == 0.0  # type: ignore
                    ):
                        input_socket.default_value = 0.0  # type: ignore

                if input_socket.is_linked:
                    # If the input socket is linked, it is likely not a scalar value
                    default_values[input_socket.name] = None
                elif input_socket.name not in default_values.keys():
                    # Store the default value of the input socket and check if it is constant across all materials
                    default_values[input_socket.name] = (i, input_socket.default_value)  # type: ignore
                elif (
                    default_values[input_socket.name] is not None
                    and default_values[input_socket.name][1]
                    != input_socket.default_value  # type: ignore
                ):
                    default_values[input_socket.name] = None

        return {k: v for k, v in default_values.items() if v is not None}

    @classmethod
    def _setup_baked_material(
        cls,
        name: str,
        baked_textures: Dict[BakeType, "bpy.types.Image"],
        shader_const_inputs: Dict[str, Any],
    ) -> "bpy.types.Material":
        import bpy

        # Create a new material
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        node_tree: bpy.types.ShaderNodeTree = mat.node_tree  # type: ignore
        nodes = node_tree.nodes
        links = node_tree.links
        nodes.clear()

        # Setup material with the Principled BSDF shader
        output_node: bpy.types.ShaderNodeOutputMaterial = nodes.new(
            type="ShaderNodeOutputMaterial"
        )  # type: ignore
        shader: bpy.types.ShaderNodeBsdfPrincipled = nodes.new(
            type="ShaderNodeBsdfPrincipled"
        )  # type: ignore
        links.new(shader.outputs["BSDF"], output_node.inputs["Surface"])

        # Setup texture coordinates using the UV map
        texcoord_node: bpy.types.ShaderNodeTexCoord = nodes.new(
            type="ShaderNodeTexCoord"
        )  # type: ignore
        mapping_node: bpy.types.ShaderNodeMapping = nodes.new(type="ShaderNodeMapping")  # type: ignore
        links.new(mapping_node.inputs["Vector"], texcoord_node.outputs["UV"])

        # Setup scalar inputs
        for i, default_value in shader_const_inputs.values():
            shader.inputs[i].default_value = default_value  # type: ignore

        # Setup all the baked textures
        for bake_type, texture in baked_textures.items():
            # Setup the image texture node
            img_texture: bpy.types.ShaderNodeTexImage = nodes.new(
                type="ShaderNodeTexImage"
            )  # type: ignore
            img_texture.image = texture
            links.new(img_texture.inputs["Vector"], mapping_node.outputs["Vector"])

            # Link the image texture to the shader node
            match bake_type:
                case BakeType.NORMAL:
                    normal_map_node: bpy.types.ShaderNodeNormalMap = nodes.new(
                        type="ShaderNodeNormalMap"
                    )  # type: ignore
                    links.new(
                        img_texture.outputs["Color"],
                        normal_map_node.inputs["Color"],
                    )
                    links.new(
                        normal_map_node.outputs["Normal"],
                        shader.inputs[
                            cls._shader_input_socket_name_from_type(bake_type)
                        ],
                    )
                case _:
                    links.new(
                        img_texture.outputs["Color"],
                        shader.inputs[
                            cls._shader_input_socket_name_from_type(bake_type)
                        ],
                    )

            if bake_type == BakeType.EMISSION:
                shader.inputs["Emission Strength"].default_value = 1.0  # type: ignore

        return mat

    @staticmethod
    def _find_shader(
        node_tree: "bpy.types.ShaderNodeTree",
    ) -> Tuple["bpy.types.ShaderNodeBsdfPrincipled", "bpy.types.ShaderNodeTree"] | None:
        import bpy

        processing_queue = [node_tree]
        while len(processing_queue) > 0:
            current_node_tree = processing_queue.pop()
            for node in current_node_tree.nodes:
                if isinstance(node, bpy.types.ShaderNodeBsdfPrincipled):
                    return node, current_node_tree
                elif isinstance(node, bpy.types.ShaderNodeGroup):
                    processing_queue.append(node.node_tree)  # type: ignore
        return None

    @staticmethod
    def _bake_pass_from_type(bake_type: BakeType) -> str:
        match bake_type:
            case BakeType.ALBEDO:
                return "DIFFUSE"
            case BakeType.EMISSION | BakeType.METALLIC:
                return "EMIT"
            case BakeType.NORMAL:
                return "NORMAL"
            case BakeType.ROUGHNESS:
                return "ROUGHNESS"

    @staticmethod
    def _shader_input_socket_name_from_type(bake_type: BakeType) -> str:
        match bake_type:
            case BakeType.ALBEDO:
                return "Base Color"
            case BakeType.EMISSION:
                return "Emission Color"
            case BakeType.METALLIC:
                return "Metallic"
            case BakeType.NORMAL:
                return "Normal"
            case BakeType.ROUGHNESS:
                return "Roughness"
