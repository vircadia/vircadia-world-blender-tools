import bpy
import os
from .. import config
from ..utils import visibility_utils

def load_export_settings(template_name):
    preset_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", template_name)
    
    settings = {}
    with open(preset_path, 'r') as file:
        for line in file:
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip().replace('op.', '')
                value = value.strip().strip("'")
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
                settings[key] = value
    
    # Remove non-export settings
    settings = {k: v for k, v in settings.items() if k.startswith('export_') or k in ['use_selection', 'use_visible', 'use_active_collection', 'use_active_scene']}
    
    return settings

def is_collision_object(obj):
    collision_keywords = ["collision", "collider", "collides", "collisions", "colliders"]
    return any(keyword in obj.name.lower() for keyword in collision_keywords)

def is_collision_or_child_of_collision(obj):
    if is_collision_object(obj):
        return True
    parent = obj.parent
    while parent:
        if is_collision_object(parent):
            return True
        parent = parent.parent
    return False

def is_keylight_object(obj):
    return "keylight" in obj.name.lower()

def is_sun_light(obj):
    return obj.type == 'LIGHT' and obj.data.type == 'SUN'

def is_other_light(obj):
    return obj.type == 'LIGHT' and obj.data.type in ['POINT', 'SPOT', 'AREA']

# Updated to treat Zone and Web as custom properties
def is_zone_object(obj):
    # Check if the object has a custom property "type" with the value "Zone"
    return obj.type == 'MESH' and obj.get('type') == 'Zone'

def is_web_object(obj):
    # Check if the object has a custom property "type" with the value "Web"
    return obj.type == 'MESH' and obj.get('type') == 'Web'

def vircadia_lightmap_data_exists():
    return "vircadia_lightmapData" in bpy.data.objects

def should_hide_in_main_export(obj):
    # Hide collision objects, keylight, sun, other lights, zones, and web objects
    if is_collision_or_child_of_collision(obj) or is_keylight_object(obj) or is_sun_light(obj):
        return True
    if vircadia_lightmap_data_exists() and is_other_light(obj):
        return True
    # Hide Zone and Web custom property objects
    if is_zone_object(obj) or is_web_object(obj):
        return True
    return False

def export_glb(context, filepath):
    print(f"Starting GLB export to {filepath}")

    # Store the original hide lightmaps state
    original_hide_lightmaps = context.scene.vircadia_hide_lightmaps

    # If hide lightmaps is False, set it to True
    if not original_hide_lightmaps:
        context.scene.vircadia_hide_lightmaps = True
        print("Hide lightmaps set to True for export")

    directory = os.path.dirname(filepath)
    filename = config.DEFAULT_GLB_EXPORT_FILENAME
    filepath = os.path.join(directory, filename)
    print(f"Full export path: {filepath}")

    # Load export settings for main export
    main_export_settings = load_export_settings("Vircadia_GLTF.py")
    main_export_settings['filepath'] = filepath
    print(f"Main export settings: {main_export_settings}")

    # Load export settings for collision export
    collision_export_settings = load_export_settings("Vircadia_Collisions.py")
    collision_filepath = filepath.replace('.glb', '_collisions.glb')
    collision_export_settings['filepath'] = collision_filepath
    print(f"Collision export settings: {collision_export_settings}")

    # Store original visibility states
    original_lod_state = context.scene.vircadia_hide_lod_levels
    original_collision_state = context.scene.vircadia_hide_collisions
    original_armature_state = context.scene.vircadia_hide_armatures

    # Unhide all objects
    context.scene.vircadia_hide_lod_levels = False
    context.scene.vircadia_hide_collisions = False
    context.scene.vircadia_hide_armatures = False
    visibility_utils.update_visibility(context.scene, context)

    hidden_objects = visibility_utils.temporarily_unhide_objects(context)

    try:
        print("Exporting main world GLB...")
        # Hide objects based on the should_hide_in_main_export function
        for obj in bpy.data.objects:
            if obj.type != 'EMPTY' and should_hide_in_main_export(obj):
                try:
                    if obj.name in context.view_layer.objects:
                        obj.hide_set(True)
                    else:
                        print(f"Object '{obj.name}' not in current View Layer, skipping hide operation")
                except Exception as e:
                    print(f"Warning: Could not hide object '{obj.name}': {str(e)}")

        bpy.ops.export_scene.gltf(**main_export_settings)
        print(f"Successfully exported main world GLB to {filepath}")

        print("Exporting collision objects GLB...")
        # Hide non-collision objects and unhide collision objects and their children
        for obj in bpy.data.objects:
            if obj.type != 'EMPTY':
                try:
                    if obj.name in context.view_layer.objects:
                        if is_collision_or_child_of_collision(obj):
                            obj.hide_set(False)
                        else:
                            obj.hide_set(True)
                    else:
                        print(f"Object '{obj.name}' not in current View Layer, skipping visibility change")
                except Exception as e:
                    print(f"Warning: Could not change visibility of object '{obj.name}': {str(e)}")

        bpy.ops.export_scene.gltf(**collision_export_settings)
        print(f"Successfully exported collision objects GLB to {collision_filepath}")

        return True
    except Exception as e:
        print(f"Error exporting GLB: {str(e)}")
        return False
    finally:
        # Restore original visibility states
        context.scene.vircadia_hide_lod_levels = original_lod_state
        context.scene.vircadia_hide_collisions = original_collision_state
        context.scene.vircadia_hide_armatures = original_armature_state
        visibility_utils.update_visibility(context.scene, context)
        visibility_utils.restore_hidden_objects(hidden_objects)

        # Restore the original hide lightmaps state
        context.scene.vircadia_hide_lightmaps = original_hide_lightmaps
        print(f"Hide lightmaps reset to its original state: {original_hide_lightmaps}")

    print("GLB export completed.")

# Add register and unregister functions to avoid the attribute error
def register():
    print("old_gltf_exporter registered")

def unregister():
    print("old_gltf_exporter unregistered")
