import bpy
from bpy.types import Operator
import os

class VIRCADIA_OT_paste_condense_script(Operator):
    bl_idname = "vircadia.paste_condense_script"
    bl_label = "Paste Script"
    bl_description = "Paste script from clipboard, preserving structure and comments"

    def execute(self, context):
        clipboard = bpy.context.window_manager.clipboard
        # Preserve all lines, including comments, and join with '\n'
        preserved_script = '\n'.join(clipboard.splitlines())
        obj = context.active_object
        obj["vircadia_script"] = preserved_script
        return {'FINISHED'}

class VIRCADIA_OT_paste_content_path(Operator):
    bl_idname = "vircadia.paste_content_path"
    bl_label = "Paste"
    bl_description = "Paste content path from clipboard and remove the file name"

    def execute(self, context):
        clipboard = bpy.context.window_manager.clipboard
        # Remove the file name from the path
        directory = os.path.dirname(clipboard)
        # Ensure the path ends with a slash
        if directory and not directory.endswith(('/', '\\')):
            directory += '/'
        context.scene.vircadia_content_path = directory
        return {'FINISHED'}

def register():
    bpy.utils.register_class(VIRCADIA_OT_paste_condense_script)
    bpy.utils.register_class(VIRCADIA_OT_paste_content_path)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_OT_paste_content_path)
    bpy.utils.unregister_class(VIRCADIA_OT_paste_condense_script)
