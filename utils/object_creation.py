import bpy
import os
from mathutils import Vector
from . import coordinate_utils, collection_utils

def extract_filename_from_url(url):
    return os.path.basename(url)

def get_blender_object_type(vircadia_type):
    type_mapping = {
        "model": "EMPTY",
        "shape": "MESH",
        "light": "LIGHT",
        "text": "FONT",
        "image": "EMPTY",
        "web": "EMPTY",
        "zone": "MESH",
        "particle": "EMPTY",
    }
    return type_mapping.get(vircadia_type.lower(), "EMPTY")

# In utils/object_creation.py

def create_blender_object(entity):
    vircadia_type = entity.get("type", "").lower()
    shape_type = entity.get("shape", "").lower()

    print(f"Creating object of type: {vircadia_type}")

    blender_type = get_blender_object_type(vircadia_type)

    # Determine the name for both the Blender object and the custom property
    if vircadia_type == "zone":
        custom_name = "Zone"
        blender_name = "Zone"
    elif vircadia_type == "model" and "modelURL" in entity:
        custom_name = extract_filename_from_url(entity["modelURL"])
        blender_name = entity.get("name", custom_name)
    else:
        custom_name = vircadia_type
        blender_name = entity.get("name", vircadia_type)

    collection = collection_utils.get_or_create_collection(vircadia_type)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]

    if vircadia_type == "zone":
        bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    elif blender_type == "MESH":
        bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    elif blender_type == "LIGHT":
        bpy.ops.object.light_add(type='POINT', location=(0, 0, 0))
    elif blender_type == "FONT":
        bpy.ops.object.text_add(location=(0, 0, 0))
    else:
        bpy.ops.object.empty_add(type='PLAIN_AXES')

    obj = bpy.context.active_object
    obj.name = blender_name

    # Set the custom "name" property
    obj["name"] = custom_name

    if "position" in entity:
        x, y, z = entity["position"].values()
        obj.location = coordinate_utils.vircadia_to_blender_coordinates(x, y, z)

    if "dimensions" in entity:
        blender_dims = coordinate_utils.vircadia_to_blender_dimensions(
            entity["dimensions"].get("x", 1),
            entity["dimensions"].get("y", 1),
            entity["dimensions"].get("z", 1)
        )
        obj.dimensions = blender_dims

    if "rotation" in entity:
        x, y, z, w = entity["rotation"].values()
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = coordinate_utils.vircadia_to_blender_rotation(x, y, z, w)

    # Set to wireframe if it's a zone or if visible is false
    if vircadia_type == "zone" or (entity.get("visible") == "false" or entity.get("visible") is False):
        obj.display_type = 'WIRE'

    # Special handling for Web entities
    if vircadia_type == "web":
        # Set dimensions directly, making it very thin in the Z direction
        if "dimensions" in entity:
            # Use the dimensions from the entity data if available
            x = entity["dimensions"].get("x", 1)
            y = entity["dimensions"].get("y", 1)
            obj.dimensions = (x, y, 0.01)
        else:
            # Default dimensions if not specified in the entity data
            obj.dimensions = (1, 1, 0.01)

    # Add update handler for transform synchronization
    bpy.app.handlers.depsgraph_update_post.append(create_transform_update_handler(obj))

    print(f"Created object: {obj.name} with custom name: {obj['name']}")
    return obj

def create_transform_update_handler(obj):
    def transform_update_handler(scene):
        if obj is None or obj.name not in bpy.data.objects:
            return

        # Update position
        vircadia_pos = coordinate_utils.blender_to_vircadia_coordinates(*obj.location)
        obj["position_x"] = vircadia_pos[0]
        obj["position_y"] = vircadia_pos[1]
        obj["position_z"] = vircadia_pos[2]

        # Update dimensions
        vircadia_dims = coordinate_utils.blender_to_vircadia_dimensions(*obj.dimensions)
        obj["dimensions_x"] = vircadia_dims[0]
        obj["dimensions_y"] = vircadia_dims[1]
        obj["dimensions_z"] = vircadia_dims[2]

        # Update rotation
        if obj.rotation_mode == 'QUATERNION':
            vircadia_rot = coordinate_utils.blender_to_vircadia_rotation(*obj.rotation_quaternion)
        else:
            vircadia_rot = coordinate_utils.blender_to_vircadia_rotation(*obj.rotation_euler.to_quaternion())
        
        obj["rotation_x"] = vircadia_rot[0]
        obj["rotation_y"] = vircadia_rot[1]
        obj["rotation_z"] = vircadia_rot[2]
        obj["rotation_w"] = vircadia_rot[3]

    return transform_update_handler

def keylight_transform_update_handler(scene):
    for obj in bpy.data.objects:
        if obj.name.startswith("keyLight_") and obj.parent and obj.parent.get("type") == "Zone":
            zone_obj = obj.parent
            direction = obj.rotation_euler.to_quaternion() @ Vector((0, 0, -1))
            zone_obj["keyLight_direction_x"] = direction.x
            zone_obj["keyLight_direction_y"] = direction.y
            zone_obj["keyLight_direction_z"] = direction.z

def transform_update_handler(scene):
    for obj in bpy.data.objects:
        if "name" in obj:
            create_transform_update_handler(obj)(scene)

def register():
    bpy.app.handlers.depsgraph_update_post.append(transform_update_handler)
    bpy.app.handlers.depsgraph_update_post.append(keylight_transform_update_handler)

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(keylight_transform_update_handler)
    bpy.app.handlers.depsgraph_update_post.remove(transform_update_handler)