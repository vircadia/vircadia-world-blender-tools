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
    grouped_properties = {group: {} for group in set(PROPERTY_GROUPS.values())}
    grouped_properties["Misc"] = {}

    for key in sorted(obj.keys()):
        if property_utils.should_filter_property(key):
            continue

        group = "Misc"
        for prefix, group_name in PROPERTY_GROUPS.items():
            if key.startswith(prefix):
                group = group_name
                break

        grouped_properties[group][key] = obj[key]

    if "Transform" in grouped_properties:
        transform_box = layout.box()
        transform_box.label(text="Transform")
        draw_transform_properties(transform_box, obj)
        del grouped_properties["Transform"]

    for group, properties in grouped_properties.items():
        if properties:
            box = layout.box()
            box.label(text=group)
            
            drawn_properties = set()
            for key, value in properties.items():
                if key in drawn_properties:
                    continue
                
                if is_color_component(key):
                    base_name = key[:-4]  # Remove '_red', '_green', or '_blue'
                    if all(f"{base_name}_{color}" in properties for color in ['red', 'green', 'blue']):
                        color_props = {color: f"{base_name}_{color}" for color in ['red', 'green', 'blue']}
                        draw_color_property(box, obj, base_name, color_props)
                        drawn_properties.update(color_props.values())
                elif is_vector_component(key):
                    base_name = key[:-2]  # Remove '_x', '_y', '_z', or '_w'
                    vector_components = ['x', 'y', 'z', 'w'] if f"{base_name}_w" in properties else ['x', 'y', 'z']
                    if all(f"{base_name}_{axis}" in properties for axis in vector_components):
                        vector_props = {axis: f"{base_name}_{axis}" for axis in vector_components}
                        draw_vector_property(box, obj, base_name, vector_props)
                        drawn_properties.update(vector_props.values())
                else:
                    draw_property(box, obj, key, key)
                    drawn_properties.add(key)

    if obj.get("type") == "Zone":
        keylight_box = layout.box()
        keylight_box.label(text="Key Light")
        draw_keylight_properties(keylight_box, obj)

def draw_property(box, obj, prop_name, full_prop_name):
    row = box.row()
    row.label(text=prop_name.capitalize())
    row.prop(obj, f'["{full_prop_name}"]', text="")

def draw_color_property(box, obj, base_name, color_components):
    row = box.row(align=True)
    row.label(text=base_name.capitalize())
    for color, label in zip(['red', 'green', 'blue'], ['R', 'G', 'B']):
        col = row.column(align=True)
        if color_components[color] in obj:
            col.prop(obj, f'["{color_components[color]}"]', text=label)

def draw_vector_property(box, obj, base_name, vector_components):
    row = box.row(align=True)
    row.label(text=base_name.capitalize())
    axes = ['w', 'x', 'y', 'z'] if 'w' in vector_components else ['x', 'y', 'z']
    for axis in axes:
        col = row.column(align=True)
        if vector_components[axis] in obj:
            col.prop(obj, f'["{vector_components[axis]}"]', text=axis.upper())

def is_color_component(key):
    return key.endswith(("_red", "_green", "_blue"))

def is_vector_component(key):
    return key.endswith(("_x", "_y", "_z", "_w"))

def draw_transform_properties(layout, obj):
    # Position
    row = layout.row(align=True)
    row.label(text="Position")
    row.prop(obj, "location", text="")

    # Rotation
    row = layout.row(align=True)
    row.label(text="Rotation")
    if obj.rotation_mode == 'QUATERNION':
        row.prop(obj, "rotation_quaternion", text="")
    else:
        row.prop(obj, "rotation_euler", text="")

    # Dimensions (Scale)
    row = layout.row(align=True)
    row.label(text="Dimensions")
    row.prop(obj, "scale", text="")

def find_keylight(zone_obj):
    for child in zone_obj.children:
        if child.name.startswith("keyLight_") and child.type == 'LIGHT':
            return child
    return None

def draw_keylight_properties(layout, zone_obj):
    keylight = find_keylight(zone_obj)
    if not keylight:
        layout.label(text="No key light found")
        return

    # Draw keyLight color
    color_props = {
        "red": "keyLight_color_red",
        "green": "keyLight_color_green",
        "blue": "keyLight_color_blue"
    }
    draw_color_property(layout, zone_obj, "Color", color_props)

    # Draw keyLight direction
    row = layout.row(align=True)
    row.label(text="Direction")
    row.prop(keylight, "rotation_euler", text="")

    # Draw keyLight intensity
    draw_property(layout, zone_obj, "Intensity", "keyLight_intensity")

def update_keylight(zone_obj):
    keylight = find_keylight(zone_obj)
    if keylight:
        # Update color
        keylight.data.color[0] = zone_obj.get("keyLight_color_red", 255) / 255
        keylight.data.color[1] = zone_obj.get("keyLight_color_green", 255) / 255
        keylight.data.color[2] = zone_obj.get("keyLight_color_blue", 255) / 255

        # Update intensity
        keylight.data.energy = zone_obj.get("keyLight_intensity", 1.0)

        # Update zone_obj custom properties with keylight rotation
        direction = keylight.rotation_euler.to_quaternion() @ bpy.data.objects['KeyLight'].matrix_world.to_3x3() @ Vector((0, 0, -1))
        zone_obj["keyLight_direction_x"] = direction.x
        zone_obj["keyLight_direction_y"] = direction.y
        zone_obj["keyLight_direction_z"] = direction.z

def keylight_update_handler(scene):
    for obj in scene.objects:
        if obj.get("type") == "Zone":
            update_keylight(obj)

def register():
    bpy.app.handlers.depsgraph_update_post.append(keylight_update_handler)

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(keylight_update_handler)