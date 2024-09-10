import bpy
import json
import os
from bpy.types import Operator
from ..utils import property_utils, collection_utils, entities

class VIRCADIA_OT_convert_to_vircadia(Operator):
    bl_idname = "vircadia.convert_to_vircadia"
    bl_label = "Convert to Vircadia"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            # Load the template_model.json template
            addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            json_path = os.path.join(addon_path, "templates", f"{entities.ENTITY_TEMPLATES_JSON['model']}")
            
            with open(json_path, 'r') as f:
                template = json.load(f)
            
            # Get the first entity from the template
            entity = template["Entities"][0]
            
            # Set custom properties
            property_utils.set_custom_properties(obj, entity)
            
            # Set the "name" custom property to the Blender object's name
            obj["name"] = obj.name

            # Set the "type" custom property
            obj["type"] = "Model"

            # Move the object to the appropriate collection
            self.move_to_type_collection(obj, "Model")
            
            self.report({'INFO'}, f"Converted {obj.name} to Vircadia entity")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No mesh object selected")
            return {'CANCELLED'}

    def move_to_type_collection(self, obj, entity_type):
        # Get or create the collection for this entity type
        collection = collection_utils.get_or_create_collection(entity_type)
        
        # Remove the object from all other collections
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        
        # Link the object to the type-specific collection
        collection.objects.link(obj)

def register():
    bpy.utils.register_class(VIRCADIA_OT_convert_to_vircadia)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_OT_convert_to_vircadia)

if __name__ == "__main__":
    register()