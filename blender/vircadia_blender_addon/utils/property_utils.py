import json

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
