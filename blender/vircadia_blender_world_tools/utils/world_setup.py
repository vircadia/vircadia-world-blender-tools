import bpy
import os

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
