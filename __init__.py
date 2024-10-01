import bpy
from . import import_export
from . import ui
from . import utils
from . import operators
from . import lightmap

bl_info = {
    "name": "Vircadia World Tools",
    "author": "Vircadia Contributors",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Vircadia",
    "description": "Create and edit Vircadia worlds in Blender",
    "category": "Import-Export",
}

def register():
    import_export.register()
    ui.register()
    utils.register()
    operators.register()
    lightmap.register()

def unregister():

    lightmap.unregister()
    operators.unregister()
    utils.unregister()
    ui.unregister()
    import_export.unregister()

if __name__ == "__main__":
    register()