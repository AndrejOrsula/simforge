from simforge.generators.blender.modifier.modifier import BlGeometryModifier


class BlDecimateModifier(BlGeometryModifier):
    def setup(self):
        raise NotImplementedError

        # # Decimate the mesh if necessary
        # if decimate_angle_limit:
        #     bpy.ops.object.modifier_add(type="DECIMATE")
        #     obj.modifiers["Decimate"].decimate_type = "DISSOLVE"
        #     obj.modifiers["Decimate"].angle_limit = decimate_angle_limit

        # if decimate_face_count:
        #     # Decimate the mesh
        #     bpy.ops.object.modifier_add(type="DECIMATE")
        #     obj.modifiers["Decimate"].ratio = decimate_face_count / len(
        #         obj.data.polygons
        #     )
        #     bpy.ops.object.modifier_apply(modifier="Decimate")
