import bpy
from ..utils import property_utils

PROPERTY_GROUPS = {
    "position": "Transform",
    "rotation": "Transform",
    "dimensions": "Transform",
    "color": "Appearance",
    "keyLight": "Lighting",
    "ambientLight": "Lighting",
    "skybox": "Environment",
    "haze": "Environment",
    "bloom": "Post-processing",
    "grab": "Interaction",
    "script": "Scripting",
    "serverScripts": "Scripting",
    "collision": "Physics",
    "dynamic": "Physics",
    "gravity": "Physics",
    "damping": "Physics",
    "angularDamping": "Physics",
    "shape": "Geometry",
    "type": "General",
    "name": "General",
    "visible": "Appearance",
    "modelURL": "Model",
    "compoundShapeURL": "Model",
    "animation": "Animation",
}

def draw_custom_properties(context, layout, obj):
    # Remove this line to avoid duplicate name display
    # layout.label(text=f"{obj.get('name', 'Unnamed')}")

    # Initialize dictionaries to hold properties for each group
    grouped_properties = {group: {} for group in set(PROPERTY_GROUPS.values())}
    grouped_properties["Misc"] = {}

    # Sort and categorize properties
    for key in sorted(obj.keys()):
        if property_utils.should_filter_property(key):
            continue

        # Determine the group for this property
        group = "Misc"
        for prefix, group_name in PROPERTY_GROUPS.items():
            if key.startswith(prefix):
                group = group_name
                break

        # Add the property to the appropriate group
        grouped_properties[group][key] = obj[key]

    # Special handling for Transform properties
    if "Transform" in grouped_properties:
        transform_box = layout.box()
        transform_box.label(text="Transform")
        draw_transform_properties(transform_box, obj)
        del grouped_properties["Transform"]

    # Draw properties for each non-empty group
    for group, properties in grouped_properties.items():
        if properties:
            box = layout.box()
            box.label(text=group)
            
            drawn_properties = set()
            for key, value in properties.items():
                if key in drawn_properties:
                    continue
                
                if is_color_component(key):
                    base_name = key.rsplit('_', 1)[0]
                    if all(f"{base_name}_{color}" in properties for color in ['red', 'green', 'blue']):
                        color_props = {color: f"{base_name}_{color}" for color in ['red', 'green', 'blue']}
                        draw_color_property(box, obj, base_name, color_props)
                        drawn_properties.update(color_props.values())
                elif is_vector_component(key):
                    base_name = key.rsplit('_', 1)[0]
                    vector_components = ['x', 'y', 'z', 'w'] if f"{base_name}_w" in properties else ['x', 'y', 'z']
                    if all(f"{base_name}_{axis}" in properties for axis in vector_components):
                        vector_props = {axis: f"{base_name}_{axis}" for axis in vector_components}
                        draw_vector_property(box, obj, base_name, vector_props)
                        drawn_properties.update(vector_props.values())
                else:
                    draw_property(box, obj, key, key)
                    drawn_properties.add(key)

    # Special handling for keyLight properties
    if "Lighting" in grouped_properties and any(key.startswith("keyLight") for key in grouped_properties["Lighting"]):
        keylight_box = layout.box()
        keylight_box.label(text="Key Light")
        draw_keylight_properties(keylight_box, obj, grouped_properties["Lighting"])

def draw_property(box, obj, prop_name, full_prop_name):
    row = box.row()
    row.label(text=prop_name.capitalize())
    row.prop(obj, f'["{full_prop_name}"]', text="")

def draw_color_property(box, obj, base_name, color_components):
    row = box.row(align=True)
    row.label(text=base_name.capitalize())
    for color, label in zip(['red', 'green', 'blue'], ['R', 'G', 'B']):
        col = row.column(align=True)
        col.prop(obj, f'["{color_components[color]}"]', text=label)

def draw_vector_property(box, obj, base_name, vector_components):
    row = box.row(align=True)
    row.label(text=base_name.capitalize())
    axes = ['w', 'x', 'y', 'z'] if 'w' in vector_components else ['x', 'y', 'z']
    for axis in axes:
        col = row.column(align=True)
        col.prop(obj, f'["{vector_components[axis]}"]', text=axis.upper())

def is_color_component(key):
    return key.endswith(("red", "green", "blue"))

def is_vector_component(key):
    return key.endswith(("x", "y", "z", "w"))

def draw_keylight_properties(layout, obj, properties):
    # Draw keyLight color
    color_props = {
        "red": properties.get("keyLight_color_red", "keyLight_color_red"),
        "green": properties.get("keyLight_color_green", "keyLight_color_green"),
        "blue": properties.get("keyLight_color_blue", "keyLight_color_blue")
    }
    draw_color_property(layout, obj, "Color", color_props)

    # Draw keyLight direction
    direction_props = {
        "x": properties.get("keyLight_direction_x", "keyLight_direction_x"),
        "y": properties.get("keyLight_direction_y", "keyLight_direction_y"),
        "z": properties.get("keyLight_direction_z", "keyLight_direction_z")
    }
    draw_vector_property(layout, obj, "Direction", direction_props)

    # Draw keyLight intensity
    intensity_prop = properties.get("keyLight_intensity", "keyLight_intensity")
    draw_property(layout, obj, "Intensity", intensity_prop)

def draw_transform_properties(layout, obj):
    # Position
    row = layout.row(align=True)
    row.label(text="Position")
    for axis in ['x', 'y', 'z']:
        row.prop(obj, f'["position_{axis}"]', text=axis.upper())

    # Rotation
    row = layout.row(align=True)
    row.label(text="Rotation")
    for axis in ['x', 'y', 'z', 'w']:
        row.prop(obj, f'["rotation_{axis}"]', text=axis.upper())

    # Dimensions
    row = layout.row(align=True)
    row.label(text="Dimensions")
    for axis in ['x', 'y', 'z']:
        row.prop(obj, f'["dimensions_{axis}"]', text=axis.upper())