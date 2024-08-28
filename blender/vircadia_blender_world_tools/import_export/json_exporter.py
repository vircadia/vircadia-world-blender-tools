import bpy
import json
from ..utils import coordinate_utils, property_utils

def get_vircadia_entity_data(obj):
    entity_data = {}

    entity_data["name"] = obj.get("name", obj.name)
    entity_data["type"] = obj.get("type", "Entity")

    blender_pos = obj.location
    vircadia_pos = coordinate_utils.blender_to_vircadia_coordinates(*blender_pos)
    entity_data["position"] = {"x": vircadia_pos[0], "y": vircadia_pos[1], "z": vircadia_pos[2]}

    blender_scale = obj.scale
    vircadia_scale = coordinate_utils.blender_to_vircadia_coordinates(*blender_scale)
    entity_data["dimensions"] = {"x": vircadia_scale[0], "y": vircadia_scale[1], "z": vircadia_scale[2]}

    if obj.rotation_mode == 'QUATERNION':
        blender_rot = obj.rotation_quaternion
        vircadia_rot = coordinate_utils.blender_to_vircadia_rotation(*blender_rot)
        entity_data["rotation"] = {"x": vircadia_rot[0], "y": vircadia_rot[1], "z": vircadia_rot[2], "w": vircadia_rot[3]}
    else:
        blender_rot = obj.rotation_euler.to_quaternion()
        vircadia_rot = coordinate_utils.blender_to_vircadia_rotation(*blender_rot)
        entity_data["rotation"] = {"x": vircadia_rot[0], "y": vircadia_rot[1], "z": vircadia_rot[2], "w": vircadia_rot[3]}

    custom_props = property_utils.get_custom_properties(obj)
    entity_data.update(custom_props)

    return entity_data

def export_vircadia_json(context, filepath):
    scene_data = {"Entities": []}

    for obj in bpy.data.objects:
        if "name" in obj:
            entity_data = get_vircadia_entity_data(obj)
            scene_data["Entities"].append(entity_data)

    with open(filepath, 'w') as f:
        json.dump(scene_data, f, indent=2)

    print(f"Vircadia JSON exported successfully to {filepath}")

def register():
    pass

def unregister():
    pass
