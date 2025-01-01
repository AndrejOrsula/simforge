import math
from pathlib import Path
from typing import Tuple

from pydantic import FiniteFloat, NonNegativeFloat, PositiveFloat, PositiveInt

from simforge import Renderer
from simforge.utils import logging


class BlThumbnailRenderer(Renderer):
    sun_rotation: Tuple[FiniteFloat, FiniteFloat, FiniteFloat] = (
        -0.25 * math.pi,
        -0.5 * math.pi,
        0.0,
    )
    sun_intensity: PositiveFloat = 100.0
    sun_angle: NonNegativeFloat = 0.0
    resolution: PositiveInt = 512

    _setup_complete: bool = False

    def setup(self):
        import bpy

        if self._setup_complete:
            logging.error("Renderer setup called multiple times")
            return
        self._setup_complete = True

        # Light
        light: bpy.types.SunLight = bpy.data.lights.new(name="Sun", type="SUN")  # type: ignore
        light_obj = bpy.data.objects.new("Sun", light)
        context: bpy.types.Context = bpy.context  # type: ignore
        context.scene.collection.objects.link(light_obj)
        light_obj.rotation_euler = self.sun_rotation
        light.energy = self.sun_intensity
        light.angle = self.sun_angle

        # Camera
        camera = bpy.data.cameras.new(name="Camera")
        camera_obj = bpy.data.objects.new("Camera", camera)
        context.scene.collection.objects.link(camera_obj)
        camera_obj.location = (0.0, 0.0, 1.0)
        scene: bpy.types.Scene = bpy.context.scene  # type: ignore
        scene.camera = camera_obj
        camera.type = "ORTHO"
        camera.clip_start = 1e-06

        # Rendering
        scene.render.film_transparent = True

    def render(self, filepath: Path):
        import bpy
        import mathutils

        # Hide all rendering of all objects except the active
        objects_to_unhide = []
        for obj in bpy.data.objects:
            if obj.type == "MESH":
                if obj != bpy.context.active_object and not obj.hide_render:  # type: ignore
                    obj.hide_render = True
                    objects_to_unhide.append(obj)
                else:
                    obj.hide_render = False

        # Determine the size of the object
        obj: bpy.types.Object = bpy.context.active_object  # type: ignore
        obj_bbox_center = obj.matrix_world @ (
            sum(
                (mathutils.Vector(b) for b in obj.bound_box),
                mathutils.Vector(),
            )
            / 8.0
        )
        obj_dims = obj.dimensions
        max_xy_dim = max(obj_dims[:2])

        # Update camera settings
        scene: bpy.types.Scene = bpy.context.scene  # type: ignore
        camera: bpy.types.Object = scene.camera  # type: ignore
        camera_data: bpy.types.Camera = camera.data  # type: ignore
        camera.location = (
            obj_bbox_center[0],
            obj_bbox_center[1],
            obj_bbox_center[2] + obj_dims[2],
        )
        camera_data.ortho_scale = max_xy_dim
        camera_data.clip_end = 2.0 * max(obj_dims[2], 1.0)

        # Update rendering setting
        scene.render.resolution_x = math.ceil(
            self.resolution * max_xy_dim / max(obj_dims[1], 0.001)
        )
        scene.render.resolution_y = math.ceil(
            self.resolution * max_xy_dim / max(obj_dims[0], 0.001)
        )
        scene.render.filepath = filepath.as_posix()
        bpy.ops.render.render(write_still=True)

        # Unhide objects
        for obj in objects_to_unhide:
            obj.hide_render = False
