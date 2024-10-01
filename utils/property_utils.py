import bpy
import json
from bpy.types import Operator
from . import coordinate_utils

# List of custom properties to skip
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
    "animation_fps",
    "keyLight_intensity",
    "keyLight_direction_x",
    "keyLight_direction_y",
    "keyLight_direction_z",
}

def should_filter_property(key):
    # Ignore ANT Landscape plugin properties and properties in the skip list
    return (key.startswith("ant_") or 
            key.startswith("Ant_") or 
            key.startswith("keyLight_color_") or 
            key in skip_properties)

def set_custom_properties(obj, data, prefix="", skip_transform=False):
    if isinstance(data, dict):
        for key, value in data.items():
            new_prefix = f"{prefix}_{key}" if prefix else key

            # Skip certain properties
            if should_filter_property(new_prefix):
                continue

            # Skip transform properties if skip_transform is True
            if skip_transform and new_prefix in ["position", "rotation", "dimensions"]:
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

def update_custom_properties_from_transform(obj):
    print(f"Vircadia: Updating custom properties for {obj.name}")
    
    # Update position custom properties
    vircadia_pos = coordinate_utils.blender_to_vircadia_coordinates(*obj.location)
    if (obj.get("position_x") != vircadia_pos[0] or 
        obj.get("position_y") != vircadia_pos[1] or 
        obj.get("position_z") != vircadia_pos[2]):
        obj["position_x"] = vircadia_pos[0]
        obj["position_y"] = vircadia_pos[1]
        obj["position_z"] = vircadia_pos[2]
        print(f"Vircadia: Updated position for {obj.name}: {vircadia_pos}")

    # Update dimensions custom properties
    vircadia_dims = coordinate_utils.blender_to_vircadia_dimensions(*obj.dimensions)
    if (obj.get("dimensions_x") != vircadia_dims[0] or 
        obj.get("dimensions_y") != vircadia_dims[1] or 
        obj.get("dimensions_z") != vircadia_dims[2]):
        obj["dimensions_x"] = vircadia_dims[0]
        obj["dimensions_y"] = vircadia_dims[1]
        obj["dimensions_z"] = vircadia_dims[2]
        print(f"Vircadia: Updated dimensions for {obj.name}: {vircadia_dims}")

    # Update rotation custom properties
    if obj.rotation_mode == 'QUATERNION':
        vircadia_rot = coordinate_utils.blender_to_vircadia_rotation(*obj.rotation_quaternion)
    else:
        vircadia_rot = coordinate_utils.blender_to_vircadia_rotation(*obj.rotation_euler.to_quaternion())
    if (obj.get("rotation_x") != vircadia_rot[0] or 
        obj.get("rotation_y") != vircadia_rot[1] or 
        obj.get("rotation_z") != vircadia_rot[2] or 
        obj.get("rotation_w") != vircadia_rot[3]):
        obj["rotation_x"] = vircadia_rot[0]
        obj["rotation_y"] = vircadia_rot[1]
        obj["rotation_z"] = vircadia_rot[2]
        obj["rotation_w"] = vircadia_rot[3]
        print(f"Vircadia: Updated rotation for {obj.name}: {vircadia_rot}")
    
    print(f"Vircadia: Custom property update completed for {obj.name}")
    
    # Force UI update
    for area in bpy.context.screen.areas:
        if area.type == 'PROPERTIES':
            area.tag_redraw()
    
    # Force UI update
    for area in bpy.context.screen.areas:
        if area.type == 'PROPERTIES':
            area.tag_redraw()
            
def custom_property_update(self, context):
    if isinstance(self, bpy.types.Object):
        update_custom_properties_from_transform(self)
    else:
        print(f"Vircadia: custom_property_update called on non-Object: {self}")

def set_initial_properties(obj, data):
    # First, set all custom properties except transform
    set_custom_properties(obj, data, skip_transform=True)
    
    # Then, update transform properties
    update_custom_properties_from_transform(obj)

# Dictionaries to store last known states and timers for objects
last_states = {}
timers = {}

class VIRCADIA_OT_force_update(Operator):
    bl_idname = "vircadia.force_update"
    bl_label = "Force Update Vircadia Entities"
    bl_description = "Force update of all Vircadia entity properties"

    def execute(self, context):
        print("Vircadia: Forcing update")
        for obj in bpy.data.objects:
            if "type" in obj:
                update_custom_properties_from_transform(obj)
        print("Vircadia: Forced update completed")
        return {'FINISHED'}

def update_handler(scene, depsgraph):
    for update in depsgraph.updates:
        if isinstance(update.id, bpy.types.Object):
            obj = update.id
            if 'type' in obj:  # Check if it's a Vircadia entity
                obj_name = obj.name

                # Initialize last state if not already stored
                if obj_name not in last_states:
                    last_states[obj_name] = {
                        'location': obj.location.copy(),
                        'rotation_euler': obj.rotation_euler.copy(),
                        'dimensions': obj.dimensions.copy(),
                    }

                # Reset the timer for this object if it exists
                if obj_name in timers:
                    try:
                        bpy.app.timers.unregister(timers[obj_name])
                    except ValueError:
                        pass  # Timer was already unregistered

                # Set a new timer to delay the update check
                def make_timer_function(obj_name):
                    def timer_func():
                        return delayed_update(obj_name)
                    return timer_func

                timer_func = make_timer_function(obj_name)
                timers[obj_name] = timer_func
                bpy.app.timers.register(timer_func, first_interval=0.5)

def delayed_update(obj_name):
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        # Object no longer exists
        return None

    last_state = last_states.get(obj_name)
    if last_state is None:
        return None

    # Check for changes in location, rotation, and dimensions
    moved = (obj.location != last_state['location'])
    rotated = (obj.rotation_euler != last_state['rotation_euler'])
    dimensions_changed = (obj.dimensions != last_state['dimensions'])

    if moved or rotated or dimensions_changed:
        update_custom_properties_from_transform(obj)

    # Update the last known state
    last_states[obj_name] = {
        'location': obj.location.copy(),
        'rotation_euler': obj.rotation_euler.copy(),
        'dimensions': obj.dimensions.copy(),
    }

    # Remove the timer entry
    if obj_name in timers:
        del timers[obj_name]

    # Return None to stop the timer
    return None

def register():
    print("Vircadia: property_utils.register() called")
    bpy.app.handlers.depsgraph_update_post.append(update_handler)
    bpy.app.handlers.load_post.append(load_post_handler)
    bpy.utils.register_class(VIRCADIA_OT_force_update)
    print(f"Vircadia: depsgraph_update_handler registered. Handler count: {len(bpy.app.handlers.depsgraph_update_post)}")

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(update_handler)
    bpy.app.handlers.load_post.remove(load_post_handler)
    bpy.utils.register_class(VIRCADIA_OT_force_update)

def load_post_handler(dummy):
    print("Vircadia: load_post_handler called")
    for obj in bpy.data.objects:
        if "type" in obj:
            update_custom_properties_from_transform(obj)
    print("Vircadia: load_post_handler completed")

if __name__ == "__main__":
    register()