import bpy
from bpy.types import Operator
from ..lightmap import generateLightmaps, lightmap_utils

class VIRCADIA_OT_generate_lightmaps(Operator):
    bl_idname = "vircadia.generate_lightmaps"
    bl_label = "Generate Lightmaps"
    bl_description = "Generate lightmaps for the selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        # Update lightmap configuration
        lightmap_settings = lightmap_utils.get_lightmap_settings(scene)
        bake_settings = lightmap_utils.get_bake_settings(scene)

        # Get visible selected objects
        visible_selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH' and not obj.hide_get()]

        if not visible_selected_objects:
            self.report({'WARNING'}, "No visible mesh objects selected. Please select at least one visible mesh object.")
            return {'CANCELLED'}

        # Generate lightmaps
        generateLightmaps.generate_lightmaps(visible_selected_objects, lightmap_settings, bake_settings)

        self.report({'INFO'}, "Lightmap generation completed")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return any(obj.type == 'MESH' and not obj.hide_get() for obj in context.selected_objects)

def register():
    bpy.utils.register_class(VIRCADIA_OT_generate_lightmaps)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_OT_generate_lightmaps)

if __name__ == "__main__":
    register()