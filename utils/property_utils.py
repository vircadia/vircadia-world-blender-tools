import json
import bpy
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
                    print(f"Failed to decode userData JSON: {value}")
            # No conversion for position and dimensions in custom properties
            elif key in ["position", "dimensions", "rotation"] and isinstance(value, dict):
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

def update_transform_from_properties(obj):
    # Update position
    if all(f"position_{axis}" in obj for axis in ['x', 'y', 'z']):
        vircadia_pos = (obj["position_x"], obj["position_y"], obj["position_z"])
        obj.location = coordinate_utils.vircadia_to_blender_coordinates(*vircadia_pos)

    # Update dimensions (scale)
    if all(f"dimensions_{axis}" in obj for axis in ['x', 'y', 'z']):
        vircadia_scale = (obj["dimensions_x"], obj["dimensions_y"], obj["dimensions_z"])
        obj.scale = coordinate_utils.vircadia_to_blender_coordinates(*vircadia_scale)

    # Update rotation
    if all(f"rotation_{axis}" in obj for axis in ['x', 'y', 'z', 'w']):
        vircadia_rot = (obj["rotation_x"], obj["rotation_y"], obj["rotation_z"], obj["rotation_w"])
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = coordinate_utils.vircadia_to_blender_rotation(*vircadia_rot)

def create_property_update_handler(obj, prop_name):
    def property_update_handler(self, context):
        update_transform_from_properties(obj)

    return property_update_handler

def register_property_update_handlers(obj):
    for prop_name in ['position_x', 'position_y', 'position_z',
                      'dimensions_x', 'dimensions_y', 'dimensions_z',
                      'rotation_x', 'rotation_y', 'rotation_z', 'rotation_w']:
        if prop_name in obj:
            obj.property_unregister(prop_name)
            obj.property_overridable_library_set(prop_name, True)
            obj.property_overridable_library_set(prop_name, True)
            obj[f"{prop_name}_update"] = create_property_update_handler(obj, prop_name)
            obj.driver_add(f'["{prop_name}"]').driver.expression = f"{prop_name}_update"

@bpy.app.handlers.persistent
def load_handler(dummy):
    for obj in bpy.data.objects:
        if "name" in obj:
            register_property_update_handlers(obj)

def register():
    bpy.app.handlers.load_post.append(load_handler)

def unregister():
    if hasattr(bpy.app.handlers, "load_post"):
        bpy.app.handlers.load_post.remove(load_handler)
        for obj in bpy.data.objects:
            if "name" in obj:
                for prop_name in ['position_x', 'position_y', 'position_z',
                                'dimensions_x', 'dimensions_y', 'dimensions_z',
                                'rotation_x', 'rotation_y', 'rotation_z', 'rotation_w']:
                    if prop_name in obj:
                        # Remove the driver if it exists
                        if obj.animation_data and obj.animation_data.drivers:
                            for driver in obj.animation_data.drivers:
                                if driver.data_path == f'["{prop_name}"]':
                                    obj.animation_data.drivers.remove(driver)
                        
                        # Remove the custom property
                        del obj[prop_name]
                    
                    # Remove the update function
                    if f"{prop_name}_update" in obj:
                        del obj[f"{prop_name}_update"]