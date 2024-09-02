from ..utils import property_utils

def draw_custom_properties(context, layout, obj):
    # Get custom properties, sort alphabetically, and filter out specific properties
    single_word_properties = {}
    grouped_properties = {}
    processed_keys = set()

    for key in sorted(obj.keys()):
        if property_utils.should_filter_property(key) or key in processed_keys:
            continue

        parts = key.split('_')
        if len(parts) == 1 or (len(parts) == 2 and len(parts[1]) == 1):
            if is_color_component(key):
                base_name = parts[0]
                if all(f"{base_name}_{color}" in obj for color in ['red', 'green', 'blue']):
                    single_word_properties[base_name] = {color: f"{base_name}_{color}" for color in ['red', 'green', 'blue']}
                    processed_keys.update(single_word_properties[base_name].values())
            elif is_vector_component(key):
                base_name = parts[0]
                vector_components = ['x', 'y', 'z']
                if f"{base_name}_w" in obj:
                    vector_components.append('w')
                if all(f"{base_name}_{axis}" in obj for axis in vector_components):
                    single_word_properties[base_name] = {axis: f"{base_name}_{axis}" for axis in vector_components}
                    processed_keys.update(single_word_properties[base_name].values())
            else:
                single_word_properties[key] = key
        else:
            group_name = parts[0]
            sub_name = "_".join(parts[1:])
            if is_color_component(key):
                base_name = "_".join(parts[:-1])
                if all(f"{base_name}_{color}" in obj for color in ['red', 'green', 'blue']):
                    if group_name not in grouped_properties:
                        grouped_properties[group_name] = {}
                    grouped_properties[group_name][base_name] = {color: f"{base_name}_{color}" for color in ['red', 'green', 'blue']}
                    processed_keys.update(grouped_properties[group_name][base_name].values())
            elif is_vector_component(key):
                base_name = "_".join(parts[:-1])
                vector_components = ['x', 'y', 'z']
                if f"{base_name}_w" in obj:
                    vector_components.append('w')
                if all(f"{base_name}_{axis}" in obj for axis in vector_components):
                    if group_name not in grouped_properties:
                        grouped_properties[group_name] = {}
                    grouped_properties[group_name][base_name] = {axis: f"{base_name}_{axis}" for axis in vector_components}
                    processed_keys.update(grouped_properties[group_name][base_name].values())
            else:
                if group_name not in grouped_properties:
                    grouped_properties[group_name] = {}
                grouped_properties[group_name][sub_name] = key

    # Draw single-word properties at the top
    for key, value in single_word_properties.items():
        if isinstance(value, dict):
            if is_color_property(value):
                draw_color_property(layout, obj, key, value)
            elif is_vector_property(value):
                draw_vector_property(layout, obj, key, value)
        else:
            draw_property(layout, obj, key, value)

    # Draw grouped properties
    for group_name, group_props in grouped_properties.items():
        box = layout.box()
        box.label(text=group_name.capitalize())

        if group_name == "keyLight":
            draw_keylight_properties(box, obj, group_props)
        else:
            for key, value in group_props.items():
                if isinstance(value, dict):
                    if is_color_property(value):
                        draw_color_property(box, obj, key, value)
                    elif is_vector_property(value):
                        draw_vector_property(box, obj, key, value)
                else:
                    draw_property(box, obj, key, value)

def draw_keylight_properties(layout, obj, properties):
    # Draw keyLight color
    color_props = {
        "red": properties.get("color", {}).get("red", "keyLight_color_red"),
        "green": properties.get("color", {}).get("green", "keyLight_color_green"),
        "blue": properties.get("color", {}).get("blue", "keyLight_color_blue")
    }
    draw_color_property(layout, obj, "Color", color_props)

    # Draw keyLight direction
    direction_props = {
        "x": properties.get("direction", {}).get("x", "keyLight_direction_x"),
        "y": properties.get("direction", {}).get("y", "keyLight_direction_y"),
        "z": properties.get("direction", {}).get("z", "keyLight_direction_z")
    }
    draw_vector_property(layout, obj, "Direction", direction_props)

    # Draw keyLight intensity
    intensity_prop = properties.get("intensity", "keyLight_intensity")
    draw_property(layout, obj, "Intensity", intensity_prop)

def is_color_component(key):
    return key.endswith(("red", "green", "blue"))

def is_vector_component(key):
    return key.endswith(("x", "y", "z", "w"))

def is_color_property(value):
    return all(color in value for color in ["red", "green", "blue"])

def is_vector_property(value):
    return all(axis in value for axis in ["x", "y", "z"])

def draw_property(layout, obj, prop_name, full_prop_name):
    row = layout.row()
    row.label(text=prop_name.capitalize())
    row.prop(obj, f'["{full_prop_name}"]', text="")

def draw_color_property(layout, obj, base_name, color_components):
    row = layout.row(align=True)
    row.label(text=base_name.capitalize())
    for color, label in zip(['red', 'green', 'blue'], ['R', 'G', 'B']):
        col = row.column(align=True)
        col.prop(obj, f'["{color_components[color]}"]', text=label)

def draw_vector_property(layout, obj, base_name, vector_components):
    row = layout.row(align=True)
    row.label(text=base_name.capitalize())
    axes = ['w', 'x', 'y', 'z'] if 'w' in vector_components else ['x', 'y', 'z']
    for axis in axes:
        col = row.column(align=True)
        col.prop(obj, f'["{vector_components[axis]}"]', text=axis.upper())