import bpy
import json
import os
from bpy.types import Operator
from ..utils import property_utils

class VIRCADIA_OT_convert_to_vircadia(Operator):
    bl_idname = "vircadia.convert_to_vircadia"
    bl_label = "Convert to Vircadia"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            # Load the models_modelOnly.json template
            addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            json_path = os.path.join(addon_path, "json_library", "models_modelOnly.json")
            
            with open(json_path, 'r') as f:
                template = json.load(f)
            
            # Get the first entity from the template
            entity = template["Entities"][0]
            
            # Set custom properties
            property_utils.set_custom_properties(obj, entity)
            
            # Set the "name" custom property to the Blender object's name
            obj["name"] = obj.name
            
            self.report({'INFO'}, f"Converted {obj.name} to Vircadia entity")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No mesh object selected")
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(VIRCADIA_OT_convert_to_vircadia)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_OT_convert_to_vircadia)

if __name__ == "__main__":
    register()
