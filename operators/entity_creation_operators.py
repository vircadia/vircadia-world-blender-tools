import bpy
import json
import os
from bpy.types import Operator

from ..utils import entities, object_creation, property_utils, coordinate_utils, collection_utils, world_setup

def get_entity_types(self, context):
    return [(t, t.capitalize(), "", i) for i, t in enumerate(entities.ENTITY_TYPES)]

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
            json_path = os.path.join(addon_path, "templates", f"{entities.ENTITY_TEMPLATES_JSON[entity_type]}")
        elif entity_type == 'image':
            json_path = os.path.join(addon_path, "templates", f"{entities.ENTITY_TEMPLATES_JSON[entity_type]}")
        elif entity_type == 'light':
            json_path = os.path.join(addon_path, "templates", f"{entities.ENTITY_TEMPLATES_JSON[entity_type]}")
        elif entity_type == 'text':
            json_path = os.path.join(addon_path, "templates", f"{entities.ENTITY_TEMPLATES_JSON[entity_type]}")
        elif entity_type == 'web':
            json_path = os.path.join(addon_path, "templates", f"{entities.ENTITY_TEMPLATES_JSON[entity_type]}")
        elif entity_type == 'zone':
            json_path = os.path.join(addon_path, "templates", f"{entities.ENTITY_TEMPLATES_JSON[entity_type]}")
        else:
            json_path = os.path.join(addon_path, "templates", f"{entities.ENTITY_TEMPLATES_JSON[entity_type]}")
        
        with open(json_path, 'r') as f:
            template = json.load(f)

        # Modify the template based on the selected type
        entity = template["Entities"][0]
        entity["type"] = entity_type.capitalize()
        if shape_type:
            entity["shape"] = shape_type.capitalize()

        # Create the Blender object
        obj = self.create_entity_object(entity, shape_type, primitive_type, context)

        if obj:
            # Set custom properties
            property_utils.set_custom_properties(obj, entity)

            # Add the object to the appropriate collection
            self.add_to_type_collection(obj, entity_type)

            # Select the new object
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj

            # Set viewport shading
            if entity_type == 'zone':
                self.set_viewport_shading(context)

        return {'FINISHED'}

    def create_entity_object(self, entity, shape_type, primitive_type, context):
        if entity["type"].lower() == "shape":
            return self.create_shape_object(entity, shape_type)
        elif entity["type"].lower() == "model":
            return self.create_model_object(entity, primitive_type)
        elif entity["type"].lower() == "image":
            return self.create_image_object(entity)
        elif entity["type"].lower() == "light":
            return self.create_light_object(entity)
        elif entity["type"].lower() == "text":
            return self.create_text_object(entity)
        elif entity["type"].lower() == "web":
            return self.create_web_object(entity)
        elif entity["type"].lower() == "zone":
            return self.create_zone_object(entity, context)
        else:
            obj = object_creation.create_blender_object(entity)
            if obj:
                # Add update callback to location, rotation, and scale properties
                obj.location.update_callback = property_utils.custom_property_update
                obj.rotation_euler.update_callback = property_utils.custom_property_update
                obj.rotation_quaternion.update_callback = property_utils.custom_property_update
                obj.scale.update_callback = property_utils.custom_property_update
            return obj

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
        obj.name = f"{shape_type.capitalize()}"
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
        obj.name = "Model"
        entity["name"] = "Model"  # Set the name in the entity dictionary

        self.set_object_properties(obj, entity)
        return obj

    def create_image_object(self, entity):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_plane_add()

        obj = bpy.context.active_object
        obj.name = "Image"
        entity["name"] = "Image"  # Set the name in the entity dictionary

        self.set_object_properties(obj, entity)
        return obj

    def create_light_object(self, entity):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.light_add(type='POINT')

        obj = bpy.context.active_object
        obj.name = "Light"
        entity["name"] = "Light"

        self.set_object_properties(obj, entity)
        return obj

    def create_text_object(self, entity):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.text_add()

        obj = bpy.context.active_object
        obj.name = "Text"
        entity["name"] = "Text"

        self.set_object_properties(obj, entity)
        return obj

    def create_web_object(self, entity):
        bpy.ops.mesh.primitive_plane_add()
        obj = bpy.context.active_object
        obj.name = "Web"
        entity["name"] = "Web"

        # Convert template dimensions to Blender coordinates
        if "dimensions" in entity:
            blender_dims = coordinate_utils.vircadia_to_blender_dimensions(
                entity["dimensions"]["x"],
                entity["dimensions"]["y"],
                entity["dimensions"]["z"]
            )
            obj.dimensions = blender_dims

        self.set_object_properties(obj, entity)
        return obj

    def create_zone_object(self, entity, context):
        # Create or get the "Zone" collection and set it as active
        zone_collection = collection_utils.get_or_create_collection("Zone")
        layer_collection = context.view_layer.layer_collection.children.get(zone_collection.name)
        context.view_layer.active_layer_collection = layer_collection

        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_cube_add()

        obj = context.active_object
        obj.name = "Zone"
        entity["name"] = "Zone"

        self.set_object_properties(obj, entity)
        obj.display_type = 'WIRE'  # Set the display type to wireframe for zones

        # Set up world lighting and keylight
        self.setup_zone_lighting(obj, context)

        return obj

    def setup_zone_lighting(self, zone_obj, context):
        addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        images_path = os.path.join(addon_path, "assets", "default", "images")

        # Set skybox texture
        skybox_texture = context.scene.vircadia_skybox_texture or os.path.join(images_path, "Skybox.jpg")
        zone_obj["skybox_url"] = skybox_texture

        # Set environment texture
        environment_texture = context.scene.vircadia_environment_texture or os.path.join(images_path, "Environment.hdr")
        zone_obj["environment_environmentTexture"] = environment_texture

        # Set up world lighting
        world_setup.setup_hdri_and_skybox(zone_obj, os.path.dirname(environment_texture))

        # Set up keylight (sun)
        self.setup_keylight(zone_obj)

    def setup_keylight(self, zone_obj):
        # The active collection is already set to "Zone", so we can create the keylight directly
        world_setup.setup_sun_light(zone_obj, bpy.context.collection)

    def set_object_properties(self, obj, entity):
        # Set position
        if "position" in entity:
            x, y, z = entity["position"].values()
            obj.location = coordinate_utils.vircadia_to_blender_coordinates(x, y, z)
            obj["position_x"] = x
            obj["position_y"] = y
            obj["position_z"] = z

        # Set dimensions
        if "dimensions" in entity:
            x, y, z = entity["dimensions"].values()
            obj.dimensions = coordinate_utils.vircadia_to_blender_dimensions(x, y, z)
            obj["dimensions_x"] = x
            obj["dimensions_y"] = y
            obj["dimensions_z"] = z

        # Set rotation
        if "rotation" in entity:
            x, y, z, w = entity["rotation"].values()
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = coordinate_utils.vircadia_to_blender_rotation(x, y, z, w)
            obj["rotation_x"] = x
            obj["rotation_y"] = y
            obj["rotation_z"] = z
            obj["rotation_w"] = w

    def add_to_type_collection(self, obj, entity_type):
        # Get or create the collection for this entity type
        collection = collection_utils.get_or_create_collection(entity_type.capitalize())
        
        # Remove the object from all other collections
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        
        # Link the object to the type-specific collection
        collection.objects.link(obj)

    def set_viewport_shading(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
                        space.shading.use_scene_lights = True
                        space.shading.use_scene_world = True
                break

def register():
    bpy.utils.register_class(VIRCADIA_OT_create_entity)
    bpy.types.Scene.vircadia_entity_type = bpy.props.EnumProperty(
        name="Entity Type",
        items=get_entity_types,
        default=0  # Set default to 0 (first item in the list)
    )

def unregister():
    bpy.utils.unregister_class(VIRCADIA_OT_create_entity)
    del bpy.types.Scene.vircadia_entity_type

if __name__ == "__main__":
    register()