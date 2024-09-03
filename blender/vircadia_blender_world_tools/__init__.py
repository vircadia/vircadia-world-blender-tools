bl_info = {
    "name": "Vircadia Blender Importer/Exporter",
    "author": "Ben Brennan",
    "version": (0, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Vircadia",
    "description": "Import and export Vircadia environments to/from Blender",
    "category": "Import-Export",
}

import bpy
from . import import_export
from . import ui
from . import utils
from . import operators

def register():
    import_export.register()
    ui.register()
    utils.register()
    operators.register()

    # Register the transform update handler
    bpy.app.handlers.depsgraph_update_post.append(utils.object_creation.transform_update_handler)

def unregister():
    # Unregister the transform update handler
    bpy.app.handlers.depsgraph_update_post.remove(utils.object_creation.transform_update_handler)

    operators.unregister()
    utils.unregister()
    ui.unregister()
    import_export.unregister()

if __name__ == "__main__":
    register()