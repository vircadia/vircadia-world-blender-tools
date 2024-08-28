import bpy
import json
from ..utils import coordinate_utils, property_utils

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def get_or_create_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    else:
        new_collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(new_collection)
        return new_collection

def extract_name_from_model_url(model_url):
    return model_url.split('/')[-1]

def create_blender_object(entity):
    vircadia_type = entity.get("type", "").lower()
    shape_type = entity.get("shapeType", "").lower()

    blender_type = get_blender_object_type(shape_type or vircadia_type)

    name = entity.get("name")
    if not name:
        model_url = entity.get("modelURL")
        if model_url:
            name = extract_name_from_model_url(model_url)
        else:
            name = f"Vircadia_{vircadia_type}"

    collection = get_or_create_collection(vircadia_type)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]

    if blender_type == "MESH":
        bpy.ops.mesh.primitive_cube_add(size=1, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    else:
        bpy.ops.object.empty_add(type='PLAIN_AXES')

    obj = bpy.context.active_object
    obj.name = name

    obj["name"] = name

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
    if vircadia_type.lower() == "zone" or (entity.get("visible") == "false" or entity.get("visible") is False):
        obj.display_type = 'WIRE'

    # Set scale to (1, 1, 1) for "model" object types
    if vircadia_type.lower() == "model":
        obj.scale = (1, 1, 1)

    return obj

def get_blender_object_type(vircadia_type):
    type_mapping = {
        "box": "MESH",
        "sphere": "MESH",
        "shape": "MESH",
    }
    return type_mapping.get(vircadia_type.lower(), "EMPTY")

def process_vircadia_json(file_path):
    data = load_json(file_path)

    for entity in data.get("Entities", []):
        obj = create_blender_object(entity)
        if obj is not None:
            property_utils.set_custom_properties(obj, entity)
        else:
            print(f"Failed to create object for entity: {entity.get('name', 'Unnamed')}")

    print("Vircadia entities imported successfully.")

def register():
    pass

def unregister():
    pass
