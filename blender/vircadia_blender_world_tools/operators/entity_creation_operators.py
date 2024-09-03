import bpy
import json
import os
from bpy.types import Operator
from ..utils import object_creation, property_utils, coordinate_utils

class VIRCADIA_OT_create_entity(Operator):
    bl_idname = "vircadia.create_entity"
    bl_label = "Create Entity"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        entity_type = context.scene.vircadia_entity_type
        shape_type = context.scene.vircadia_shape_type if entity_type == 'shape' else None
        primitive_type = context.scene.vircadia_primitive_type if entity_type == 'model' else None

        # Load the appropriate template JSON based on entity type
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        if entity_type == 'model':
            json_path = os.path.join(addon_path, "json_library", "models_modelOnly.json")
        elif entity_type == 'image':
            json_path = os.path.join(addon_path, "json_library", "models_imageOnly.json")
        else:
            json_path = os.path.join(addon_path, "json_library", "models_shapeOnly.json")
        
        with open(json_path, 'r') as f:
            template = json.load(f)

        # Modify the template based on the selected type
        entity = template["Entities"][0]
        entity["type"] = entity_type.capitalize()
        if shape_type:
            entity["shape"] = shape_type.capitalize()

        # Create the Blender object
        obj = self.create_entity_object(entity, shape_type, primitive_type)

        if obj:
            # Set custom properties
            property_utils.set_custom_properties(obj, entity)

            # Select the new object
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

        return {'FINISHED'}

    def create_entity_object(self, entity, shape_type, primitive_type):
        if entity["type"].lower() == "shape":
            return self.create_shape_object(entity, shape_type)
        elif entity["type"].lower() == "model":
            return self.create_model_object(entity, primitive_type)
        elif entity["type"].lower() == "image":
            return self.create_image_object(entity)
        else:
            return object_creation.create_blender_object(entity)

    def create_shape_object(self, entity, shape_type):
        bpy.ops.object.select_all(action='DESELECT')
        
        if shape_type == 'box':
            bpy.ops.mesh.primitive_cube_add()
        elif shape_type == 'sphere':
            bpy.ops.mesh.primitive_uv_sphere_add()
        elif shape_type == 'isosahedron':
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1)
        elif shape_type == 'hexagon':
            bpy.ops.mesh.primitive_cylinder_add(vertices=6)
        elif shape_type == 'octagon':
            bpy.ops.mesh.primitive_cylinder_add(vertices=8)
        elif shape_type == 'cylinder':
            bpy.ops.mesh.primitive_cylinder_add()
        elif shape_type == 'cone':
            bpy.ops.mesh.primitive_cone_add()
        elif shape_type == 'circle':
            bpy.ops.mesh.primitive_circle_add()
        elif shape_type == 'quad':
            bpy.ops.mesh.primitive_plane_add()

        obj = bpy.context.active_object
        obj.name = f"Vircadia_{shape_type.capitalize()}"
        entity["name"] = shape_type.capitalize()  # Set the name in the entity dictionary

        self.set_object_properties(obj, entity)
        return obj

    def create_model_object(self, entity, primitive_type):
        bpy.ops.object.select_all(action='DESELECT')

        if primitive_type == 'PLANE':
            bpy.ops.mesh.primitive_plane_add()
        elif primitive_type == 'CUBE':
            bpy.ops.mesh.primitive_cube_add()
        elif primitive_type == 'CIRCLE':
            bpy.ops.mesh.primitive_circle_add()
        elif primitive_type == 'UVSPHERE':
            bpy.ops.mesh.primitive_uv_sphere_add()
        elif primitive_type == 'ICOSPHERE':
            bpy.ops.mesh.primitive_ico_sphere_add()
        elif primitive_type == 'CYLINDER':
            bpy.ops.mesh.primitive_cylinder_add()
        elif primitive_type == 'CONE':
            bpy.ops.mesh.primitive_cone_add()
        elif primitive_type == 'TORUS':
            bpy.ops.mesh.primitive_torus_add()
        elif primitive_type == 'MONKEY':
            bpy.ops.mesh.primitive_monkey_add()

        obj = bpy.context.active_object
        obj.name = f"Vircadia_{primitive_type.capitalize()}"
        entity["name"] = primitive_type.capitalize()  # Set the name in the entity dictionary

        self.set_object_properties(obj, entity)
        return obj

    def create_image_object(self, entity):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_plane_add()

        obj = bpy.context.active_object
        obj.name = "Vircadia_Image"
        entity["name"] = "Image"  # Set the name in the entity dictionary

        self.set_object_properties(obj, entity)
        return obj

    def set_object_properties(self, obj, entity):
        # Set position
        if "position" in entity:
            x, y, z = entity["position"].values()
            obj.location = coordinate_utils.vircadia_to_blender_coordinates(x, y, z)

        # Set dimensions
        if "dimensions" in entity:
            x, y, z = entity["dimensions"].values()
            obj.scale = coordinate_utils.vircadia_to_blender_coordinates(x, y, z)

        # Set rotation
        if "rotation" in entity:
            x, y, z, w = entity["rotation"].values()
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = coordinate_utils.vircadia_to_blender_rotation(x, y, z, w)

def register():
    bpy.utils.register_class(VIRCADIA_OT_create_entity)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_OT_create_entity)

if __name__ == "__main__":
    register()
