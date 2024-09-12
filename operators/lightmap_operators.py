import bpy
from bpy.types import Operator
from ..lightmap import generate_lightmaps, lightmap_utils

class VIRCADIA_OT_generate_lightmaps(Operator):
    bl_idname = "vircadia.generate_lightmaps"
    bl_label = "Generate Lightmaps"
    bl_description = "Generate lightmaps for the selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene

        # Update lightmap configuration
        lightmap_utils.COLOR_SPACE = scene.vircadia_lightmap_color_space
        lightmap_utils.RESOLUTION_SINGLE = scene.vircadia_lightmap_resolution_single
        lightmap_utils.RESOLUTION_SMALL_GROUP = scene.vircadia_lightmap_resolution_small
        lightmap_utils.RESOLUTION_LARGE_GROUP = scene.vircadia_lightmap_resolution_large
        lightmap_utils.SMALL_GROUP_THRESHOLD = scene.vircadia_lightmap_small_threshold
        lightmap_utils.LARGE_GROUP_THRESHOLD = scene.vircadia_lightmap_large_threshold

        # Update bake settings
        bake_settings = {}
        for setting in lightmap_utils.BAKE_SETTINGS_WHITELIST:
            bake_settings[setting] = getattr(scene, f"vircadia_lightmap_{setting}")
        lightmap_utils.apply_bake_settings(bake_settings)

        # Generate lightmaps
        generate_lightmaps()

        self.report({'INFO'}, "Lightmap generation completed")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

def register():
    bpy.utils.register_class(VIRCADIA_OT_generate_lightmaps)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_OT_generate_lightmaps)

if __name__ == "__main__":
    register()