import bpy
import os
from mathutils import Vector, Euler, Quaternion
from ..utils import coordinate_utils

def setup_hdri_and_skybox(zone_obj, json_directory):
    # Set up the World shader nodes
    world = bpy.context.scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Clear existing nodes
    nodes.clear()

    # Create nodes
    node_output = nodes.new(type='ShaderNodeOutputWorld')
    node_background_lighting = nodes.new(type='ShaderNodeBackground')
    node_background_skybox = nodes.new(type='ShaderNodeBackground')
    node_env_lighting = nodes.new(type='ShaderNodeTexEnvironment')
    node_env_background = nodes.new(type='ShaderNodeTexEnvironment')
    node_light_path = nodes.new(type='ShaderNodeLightPath')
    node_mix = nodes.new(type='ShaderNodeMixShader')

    # Set up HDRI for lighting
    hdri_filename = zone_obj.get("environment_environmentTexture", "")
    if hdri_filename:
        hdri_path = os.path.normpath(os.path.join(json_directory, os.path.basename(hdri_filename)))
        if os.path.exists(hdri_path):
            node_env_lighting.image = bpy.data.images.load(hdri_path)
        else:
            print(f"Warning: HDRI file not found: {hdri_path}")
    else:
        print("Warning: environment_environmentTexture not found in zone entity.")

    # Set up background image
    skybox_filename = zone_obj.get("skybox_url", "")
    if skybox_filename:
        background_path = os.path.normpath(os.path.join(json_directory, os.path.basename(skybox_filename)))
        if os.path.exists(background_path):
            node_env_background.image = bpy.data.images.load(background_path)
        else:
            print(f"Warning: Skybox file not found: {background_path}")
    else:
        print("Warning: skybox_url not found in zone entity.")

    # Connect nodes
    links.new(node_env_lighting.outputs["Color"], node_background_lighting.inputs["Color"])
    links.new(node_env_background.outputs["Color"], node_background_skybox.inputs["Color"])
    links.new(node_background_lighting.outputs["Background"], node_mix.inputs[1])
    links.new(node_background_skybox.outputs["Background"], node_mix.inputs[2])
    links.new(node_light_path.outputs["Is Camera Ray"], node_mix.inputs["Fac"])
    links.new(node_mix.outputs["Shader"], node_output.inputs["Surface"])

    # Arrange nodes in the shader editor
    node_output.location = (300, 0)
    node_mix.location = (100, 0)
    node_background_lighting.location = (-100, 100)
    node_background_skybox.location = (-100, -100)
    node_env_lighting.location = (-300, 100)
    node_env_background.location = (-300, -100)
    node_light_path.location = (-300, 0)

    # Set up the sun light
    setup_sun_light(zone_obj)

def setup_sun_light(zone_obj):
    # Create a new sun light
    sun_light = bpy.data.lights.new(name=f"keyLight_{zone_obj.name}", type='SUN')
    sun_object = bpy.data.objects.new(name=f"keyLight_{zone_obj.name}", object_data=sun_light)

    # Link the sun to the zone collection
    zone_collection = zone_obj.users_collection[0]
    zone_collection.objects.link(sun_object)

    # Parent the sun to the zone
    sun_object.parent = zone_obj

    # Set the sun color
    update_sun_color(zone_obj, sun_light)

    # Set the sun direction
    update_sun_direction(zone_obj, sun_object)

    # Set visibility based on keyLightMode
    key_light_mode = zone_obj.get("keyLightMode", True)
    sun_object.hide_viewport = not key_light_mode
    sun_object.hide_render = not key_light_mode

    # Set intensity
    sun_light.energy = zone_obj.get("keyLight_intensity", 1.0)

    # Add any additional keyLight properties
    for prop, value in zone_obj.items():
        if prop.startswith("keyLight") and prop not in ["keyLight_color_red", "keyLight_color_green", "keyLight_color_blue", "keyLight_direction_x", "keyLight_direction_y", "keyLight_direction_z", "keyLightMode", "keyLight_intensity"]:
            sun_object[prop] = value

    print(f"Sun light setup complete for {zone_obj.name}")

def update_sun_color(zone_obj, sun_light):
    red = zone_obj.get("keyLight_color_red", 255) / 255
    green = zone_obj.get("keyLight_color_green", 255) / 255
    blue = zone_obj.get("keyLight_color_blue", 255) / 255
    sun_light.color = (red, green, blue)
    print(f"Updated sun color: R={red}, G={green}, B={blue}")

def update_sun_direction(zone_obj, sun_object):
    direction_x = zone_obj.get("keyLight_direction_x", 0)
    direction_y = zone_obj.get("keyLight_direction_y", 0)
    direction_z = zone_obj.get("keyLight_direction_z", 0)

    # Use the direction directly without conversion
    sun_object.rotation_euler = Vector((direction_x, direction_y, direction_z)).to_track_quat('-Z', 'Y').to_euler()
    print(f"Updated sun direction: X={direction_x}, Y={direction_y}, Z={direction_z}")

def update_keylight(zone_obj):
    keylight_name = f"keyLight_{zone_obj.name}"
    keylight = bpy.data.objects.get(keylight_name)

    if keylight:
        update_sun_color(zone_obj, keylight.data)
        update_sun_direction(zone_obj, keylight)
        keylight.data.energy = zone_obj.get("keyLight_intensity", 1.0)
        print(f"Updated keylight {keylight_name} based on zone properties")

def update_keylight_from_sun(sun_object):
    zone_obj = sun_object.parent
    if zone_obj:
        print(f"Updating keyLight properties for {zone_obj.name}")
        # Update color
        zone_obj["keyLight_color_red"] = int(sun_object.data.color[0] * 255)
        zone_obj["keyLight_color_green"] = int(sun_object.data.color[1] * 255)
        zone_obj["keyLight_color_blue"] = int(sun_object.data.color[2] * 255)
        print(f"Updated color: R={zone_obj['keyLight_color_red']}, G={zone_obj['keyLight_color_green']}, B={zone_obj['keyLight_color_blue']}")

        # Convert Blender rotation back to Vircadia direction
        direction = sun_object.rotation_euler.to_quaternion() @ Vector((0, 0, -1))
        zone_obj["keyLight_direction_x"] = direction.x
        zone_obj["keyLight_direction_y"] = direction.y
        zone_obj["keyLight_direction_z"] = direction.z
        print(f"Updated direction: X={zone_obj['keyLight_direction_x']}, Y={zone_obj['keyLight_direction_y']}, Z={zone_obj['keyLight_direction_z']}")

        # Update intensity
        zone_obj["keyLight_intensity"] = sun_object.data.energy
        print(f"Updated intensity: {zone_obj['keyLight_intensity']}")

def keylight_update_handler(scene):
    for obj in scene.objects:
        if obj.get("type") == "Zone":
            update_keylight(obj)

def handle_sun_updates(scene):
    for obj in scene.objects:
        if obj.type == 'LIGHT' and obj.data.type == 'SUN' and obj.parent and obj.parent.get("type") == "Zone":
            update_keylight_from_sun(obj)

def set_viewport_shading():
    # Set viewport shading to Material Preview
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    space.shading.use_scene_world = True
                    space.shading.use_scene_lights = True
            break  # Assuming there's only one 3D View, we can break after setting it

    # Set color management view transform to standard
    bpy.context.scene.view_settings.view_transform = 'Standard'

def configure_world_and_viewport():
    set_viewport_shading()
    # Additional world setup can be added here if needed

def register():
    bpy.app.handlers.depsgraph_update_post.append(handle_sun_updates)
    bpy.app.handlers.depsgraph_update_post.append(keylight_update_handler)

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(handle_sun_updates)
    bpy.app.handlers.depsgraph_update_post.remove(keylight_update_handler)

print("world_setup.py loaded")