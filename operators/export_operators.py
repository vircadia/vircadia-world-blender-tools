import bpy
import os
import logging
from ..import_export import old_json_exporter, gltf_exporter
from .. import config
from ..ui.tooltips import ImportExportTooltips

class EXPORT_OT_vircadia_json(bpy.types.Operator):
    bl_idname = "export_scene.vircadia_json"
    bl_label = "Export Vircadia JSON"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    bl_description = ImportExportTooltips.EXPORT_JSON 

    def execute(self, context):
        logging.info("Executing JSON export")
        
        # Check if content path is set
        if not context.scene.vircadia_content_path:
            self.report({'ERROR'}, "Content Path is not set. Please set it in the World Properties panel before exporting.")
            return {'CANCELLED'}
        
        try:
            old_json_exporter.export_vircadia_json(context, self.filepath)
            self.report({'INFO'}, f"Vircadia JSON exported successfully to {self.filepath}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error exporting JSON: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        logging.info("Invoking JSON export")
        self.filepath = os.path.join(os.path.dirname(bpy.data.filepath), config.DEFAULT_JSON_EXPORT_FILENAME)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class EXPORT_OT_vircadia_glb(bpy.types.Operator):
    bl_idname = "export_scene.vircadia_glb"
    bl_label = "Export Vircadia GLB"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    bl_description = ImportExportTooltips.EXPORT_GLB

    def execute(self, context):
        logging.info("Executing GLB export")
        success = gltf_exporter.export_glb(context, self.filepath)
        if success:
            self.report({'INFO'}, f"GLB exported successfully to {self.filepath}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to export GLB")
            return {'CANCELLED'}

    def invoke(self, context, event):
        logging.info("Invoking GLB export")
        self.filepath = os.path.join(os.path.dirname(self.filepath), config.DEFAULT_GLB_EXPORT_FILENAME)
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(EXPORT_OT_vircadia_json)
    bpy.utils.register_class(EXPORT_OT_vircadia_glb)

def unregister():
    bpy.utils.unregister_class(EXPORT_OT_vircadia_glb)
    bpy.utils.unregister_class(EXPORT_OT_vircadia_json)