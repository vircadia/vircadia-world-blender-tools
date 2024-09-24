import bpy
import json
from . import coordinate_utils

# List of properties to skip
skip_properties = {
    "DataVersion",
    "Version",
    "created",
    "lastEditedBy",
    "lastEdited",
    "keyLight_shadowMaxDistance",
    "keyLight_shadowBias",
    "keyLight_castShadows",
    "avatarEntity",
    "localEntity",
    "isFacingAvatar",
    "clientOnly",
    "faceCamera",
    "grab",
    "bloom",
    "ambientLight",
    "gravity",
    "queryAACube",
    "groupCulled"
    "href"
    "ID"
    "modelURL"
    "cloneable"
    "cloneLifetime"
    "cloneDynamic"
    "cloneAvatarEntity"
    "canCastShadow"
    "blendshapeCoefficients"
    "angularDamping"
    "animation_currentFrame"
    "animation_firstFrame"
    "animation_fps"
}

def should_filter_property(key):
    # Ignore ANT Landscape plugin properties and properties in the skip list
    return (key.startswith("ant_") or 
            key.startswith("Ant_") or 
            key in skip_properties)

def set_custom_properties(obj, data, prefix=""):
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}_{key}" if prefix else key

            # Skip certain properties
            if should_filter_property(new_prefix):
                continue

            # Special handling for "userData"
            if key == "userData" and isinstance(value, str):
                try:
                    user_data_json = json.loads(value)
                    set_custom_properties(obj, user_data_json, "")  # Remove prefix for userData
                except json.JSONDecodeError:
                    print(f"Note: userData is not valid JSON, storing as string: {value}")
                    obj[new_prefix] = value
            # Special handling for dimensions
            elif key == "dimensions" and isinstance(value, dict):
                blender_dims = coordinate_utils.vircadia_to_blender_dimensions(
                    value.get('x', 0), value.get('y', 0), value.get('z', 0)
                )
                obj.dimensions = blender_dims
                # Still set custom properties for compatibility
                for axis, axis_value in zip(['x', 'y', 'z'], blender_dims):
                    obj[f"{new_prefix}_{axis}"] = axis_value
            # No conversion for position in custom properties
            elif key in ["position", "rotation"] and isinstance(value, dict):
                for axis, axis_value in value.items():
                    set_custom_properties(obj, axis_value, f"{new_prefix}_{axis}")
            else:
                set_custom_properties(obj, value, new_prefix)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_prefix = f"{prefix}_{i}"
            set_custom_properties(obj, item, new_prefix)
    else:
        # Remove existing property if it exists
        if prefix in obj:
            del obj[prefix]

        # Handle different data types for properties
        if isinstance(data, bool):
            obj[prefix] = data
        elif isinstance(data, int):
            if -2**31 <= data <= 2**31-1:
                if any(color in prefix.lower() for color in ["red", "green", "blue"]):
                    obj[prefix] = data
                    rna_prop = obj.id_properties_ui(prefix)
                    rna_prop.update(min=0, max=255)
                else:
                    obj[prefix] = data
            else:
                obj[prefix] = str(data)  # Store large integers as strings
        elif isinstance(data, float):
            obj[prefix] = data
        elif isinstance(data, str):
            # Check if the value is "enabled" or "disabled"
            if data.lower() in ["enabled", "disabled"]:
                obj[prefix] = (data.lower() == "enabled")
            else:
                obj[prefix] = data

def get_custom_properties(obj):
    properties = {}
    for key in obj.keys():
        if not should_filter_property(key):
            properties[key] = obj[key]
    return properties

def update_blender_transform_from_properties(obj):
    # Update position
    if all(f"position_{axis}" in obj for axis in ['x', 'y', 'z']):
        vircadia_pos = (obj["position_x"], obj["position_y"], obj["position_z"])
        obj.location = coordinate_utils.vircadia_to_blender_coordinates(*vircadia_pos)

    # Update dimensions
    if all(f"dimensions_{axis}" in obj for axis in ['x', 'y', 'z']):
        vircadia_dims = (obj["dimensions_x"], obj["dimensions_y"], obj["dimensions_z"])
        if obj.get("type") == "Web":
            obj.dimensions = (vircadia_dims[0], vircadia_dims[2], 0.01)  # Web entities use Y as Z
        else:
            obj.dimensions = coordinate_utils.vircadia_to_blender_dimensions(*vircadia_dims)

    # Update rotation
    if all(f"rotation_{axis}" in obj for axis in ['x', 'y', 'z', 'w']):
        vircadia_rot = (obj["rotation_x"], obj["rotation_y"], obj["rotation_z"], obj["rotation_w"])
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = coordinate_utils.vircadia_to_blender_rotation(*vircadia_rot)

def update_custom_properties_from_transform(obj):
    # Update position custom properties
    vircadia_pos = coordinate_utils.blender_to_vircadia_coordinates(*obj.location)
    obj["position_x"] = vircadia_pos[0]
    obj["position_y"] = vircadia_pos[1]
    obj["position_z"] = vircadia_pos[2]

    # Update dimensions custom properties
    if obj.get("type") == "Web":
        obj["dimensions_x"] = obj.dimensions.x
        obj["dimensions_y"] = obj.dimensions.z  # Web entities use Y as Z
        obj["dimensions_z"] = 0.01
    else:
        vircadia_dims = coordinate_utils.blender_to_vircadia_dimensions(*obj.dimensions)
        obj["dimensions_x"] = vircadia_dims[0]
        obj["dimensions_y"] = vircadia_dims[1]
        obj["dimensions_z"] = vircadia_dims[2]

    # Update rotation custom properties
    vircadia_rot = coordinate_utils.blender_to_vircadia_rotation(*obj.rotation_quaternion)
    obj["rotation_x"] = vircadia_rot[0]
    obj["rotation_y"] = vircadia_rot[1]
    obj["rotation_z"] = vircadia_rot[2]
    obj["rotation_w"] = vircadia_rot[3]

def depsgraph_update_handler(scene):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for update in depsgraph.updates:
        if isinstance(update.id, bpy.types.Object):
            obj = update.id
            if "name" in obj:  # Check if it's a Vircadia entity
                if update.is_updated_transform:
                    update_custom_properties_from_transform(obj)

def load_handler(dummy):
    for obj in bpy.data.objects:
        if "name" in obj:
            update_custom_properties_from_transform(obj)

def register():
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_handler)
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_handler)
    bpy.app.handlers.load_post.remove(load_handler)

print("property_utils.py loaded")