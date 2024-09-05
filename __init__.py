# Add this at the beginning of your file
if "bpy" in locals():
    import importlib
    if "import_export" in locals():
        importlib.reload(import_export)
    if "ui" in locals():
        importlib.reload(ui)
    if "utils" in locals():
        importlib.reload(utils)
    if "operators" in locals():
        importlib.reload(operators)

import bpy
from . import import_export
from . import ui
from . import utils
from . import operators

bl_info = {
    "name": "Vircadia World Tools",
    "author": "Vircadia Contributors",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Vircadia",
    "description": "Create and edit Vircadia worlds in Blender",
    "category": "Import-Export",
}

class VIRCADIA_OT_reload_addon(bpy.types.Operator):
    bl_idname = 'wm.vircadia_reload_addon'
    bl_label = 'Reload Vircadia World Tools'

    def execute(self, context):
        import importlib
        import sys

        # Unregister all modules
        unregister()

        # Reload all modules
        for module in list(sys.modules):
            if module.startswith(__package__ + '.'):
                importlib.reload(sys.modules[module])

        # Re-register all modules
        register()
        
        return {'FINISHED'}

def register():
    # if not hasattr(bpy.utils, VIRCADIA_OT_reload_addon.__name__):
    bpy.utils.register_class(VIRCADIA_OT_reload_addon)
    import_export.register()
    ui.register()
    utils.register()
    operators.register()

    # Register the transform update handler
    if utils.object_creation.global_transform_update_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(utils.object_creation.global_transform_update_handler)

def unregister():
    # Unregister the transform update handler
    if utils.object_creation.global_transform_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(utils.object_creation.global_transform_update_handler)

    operators.unregister()
    utils.unregister()
    ui.unregister()
    import_export.unregister()
    # if hasattr(bpy.utils, VIRCADIA_OT_reload_addon.__name__):
    bpy.utils.unregister_class(VIRCADIA_OT_reload_addon)

if __name__ == "__main__":
    register()