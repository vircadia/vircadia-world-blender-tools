import bpy
from ..import_export import old_json_exporter, gltf_exporter

class EXPORT_OT_vircadia_json(bpy.types.Operator):
    bl_idname = "export_scene.vircadia_json"
    bl_label = "Export Vircadia JSON"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        old_json_exporter.export_vircadia_json(context, self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class EXPORT_OT_vircadia_gltf(bpy.types.Operator):
    bl_idname = "export_scene.vircadia_gltf"
    bl_label = "Export Vircadia GLTF"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        gltf_exporter.export_glb(context, self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(EXPORT_OT_vircadia_json)
    bpy.utils.register_class(EXPORT_OT_vircadia_gltf)

def unregister():
    bpy.utils.unregister_class(EXPORT_OT_vircadia_gltf)
    bpy.utils.unregister_class(EXPORT_OT_vircadia_json)
