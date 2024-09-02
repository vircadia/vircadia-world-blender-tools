import bpy
import os
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
        "zone": "EMPTY",
        "particle": "EMPTY",
    }
    return type_mapping.get(vircadia_type.lower(), "EMPTY")

def create_blender_object(entity):
    vircadia_type = entity.get("type", "").lower()
    shape_type = entity.get("shape", "").lower()

    print(f"Creating object of type: {vircadia_type}")

    blender_type = get_blender_object_type(vircadia_type)

    # Determine the name for both the Blender object and the custom property
    if vircadia_type == "zone":
        custom_name = "zone"
        blender_name = "zone"
    elif vircadia_type == "model" and "modelURL" in entity:
        custom_name = extract_filename_from_url(entity["modelURL"])
        blender_name = entity.get("name", custom_name)
    else:
        custom_name = vircadia_type
        blender_name = entity.get("name", vircadia_type)

    collection = collection_utils.get_or_create_collection(vircadia_type)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]

    if blender_type == "MESH":
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
        x, y, z = entity["dimensions"].values()
        obj.scale = coordinate_utils.vircadia_to_blender_coordinates(x, y, z)

    if "rotation" in entity:
        x, y, z, w = entity["rotation"].values()
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = coordinate_utils.vircadia_to_blender_rotation(x, y, z, w)

    # Set to wireframe if it's a zone or if visible is false
    if vircadia_type == "zone" or (entity.get("visible") == "false" or entity.get("visible") is False):
        obj.display_type = 'WIRE'

    # Set scale to (1, 1, 1) for "model" object types
    if vircadia_type == "model":
        obj.scale = (1, 1, 1)

    print(f"Created object: {obj.name} with custom name: {obj['name']}")
    return obj