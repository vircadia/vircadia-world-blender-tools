bl_info = {
    "name": "Vircadia Blender World Tools",
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
    operators.register()

def unregister():
    operators.unregister()
    ui.unregister()
    import_export.unregister()

if __name__ == "__main__":
    register()
