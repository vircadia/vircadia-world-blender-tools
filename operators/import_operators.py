import bpy
import os
from bpy_extras.io_utils import ImportHelper
from bpy.props import CollectionProperty, StringProperty
from bpy.types import Operator
from ..import_export import old_json_importer, gltf_importer

class IMPORT_OT_vircadia_json(bpy.types.Operator):
    bl_idname = "import_scene.vircadia_json"
    bl_label = "Import Vircadia JSON"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        try:
            old_json_importer.process_vircadia_json(self.filepath)
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error importing JSON: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class IMPORT_OT_vircadia_gltf(Operator, ImportHelper):
    bl_idname = "import_scene.vircadia_gltf"
    bl_label = "Import Vircadia GLTF"
    
    files: CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
    )
    
    directory: StringProperty(subtype='DIR_PATH')
    
    filename_ext = ".glb;.gltf"
    filter_glob: StringProperty(default="*.glb;*.gltf", options={'HIDDEN'})

    def execute(self, context):
        filepaths = [os.path.join(self.directory, name.name) for name in self.files]
        gltf_importer.import_gltf_or_glb(context, filepaths)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(IMPORT_OT_vircadia_json)
    bpy.utils.register_class(IMPORT_OT_vircadia_gltf)

def unregister():
    bpy.utils.unregister_class(IMPORT_OT_vircadia_gltf)
    bpy.utils.unregister_class(IMPORT_OT_vircadia_json)
