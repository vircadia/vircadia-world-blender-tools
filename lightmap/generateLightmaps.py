import bpy
import bmesh
from collections import defaultdict

# Dictionary to store created image texture nodes
created_nodes = {}

# Dictionary to store objects sharing the same material
material_to_objects = defaultdict(list)

# Dictionary to store original UV states
original_uv_states = {}

def make_single_user(obj):
    if obj.data.users > 1:
        new_mesh = obj.data.copy()
        obj.data = new_mesh

def store_original_uv_state(obj):
    mesh = obj.data
    original_uv_states[obj.name] = {
        "active": mesh.uv_layers.active.name if mesh.uv_layers.active else None,
        "render": next((uv.name for uv in mesh.uv_layers if uv.active_render), None)
    }

def ensure_uv_maps(obj):
    mesh = obj.data
    if len(mesh.uv_layers) == 0:
        new_uv = mesh.uv_layers.new(name="UVMap")
        new_uv.active = True
        new_uv.active_render = True
    
    if len(mesh.uv_layers) == 1:
        lightmap_uv = mesh.uv_layers.new(name="Lightmap")
        lightmap_uv.active = True
        lightmap_uv.active_render = True
        return lightmap_uv
    
    if mesh.uv_layers[1].name == "Lightmap":
        lightmap_uv = mesh.uv_layers[1]
        lightmap_uv.active = True
        lightmap_uv.active_render = True
        return lightmap_uv
    
    # Store existing UV map data
    existing_uv_data = [uv_loop.uv.copy() for uv_loop in mesh.uv_layers[1].data]
    existing_uv_name = mesh.uv_layers[1].name
    
    # Remove existing UV map in slot 1
    mesh.uv_layers.remove(mesh.uv_layers[1])
    
    # Create new Lightmap UV
    lightmap_uv = mesh.uv_layers.new(name="Lightmap")
    lightmap_uv.active = True
    lightmap_uv.active_render = True
    
    # Add stored UV map data to slot 2
    stored_uv = mesh.uv_layers.new(name=existing_uv_name)
    for i, uv_loop in enumerate(stored_uv.data):
        uv_loop.uv = existing_uv_data[i]
    
    return lightmap_uv

def restore_original_uv_states():
    for obj_name, uv_state in original_uv_states.items():
        obj = bpy.data.objects.get(obj_name)
        if obj and obj.type == 'MESH':
            mesh = obj.data
            if uv_state["active"] and uv_state["active"] in mesh.uv_layers:
                mesh.uv_layers.active = mesh.uv_layers[uv_state["active"]]
            if uv_state["render"] and uv_state["render"] in mesh.uv_layers:
                for uv in mesh.uv_layers:
                    uv.active_render = (uv.name == uv_state["render"])

def deselect_all_nodes(nodes):
    for node in nodes:
        node.select = False
    nodes.active = None

def find_or_create_image_texture(mat, obj_name, resolution, color_space):
    global created_nodes
    nodes = mat.node_tree.nodes

    # Deselect all nodes and set active node to None
    deselect_all_nodes(nodes)

    # Check if we've already created a node for this material
    if mat.name in created_nodes:
        node = created_nodes[mat.name]
        node.select = True
        nodes.active = node
        return node

    # Look for existing Lightmap node
    for node in nodes:
        if node.type == 'TEX_IMAGE' and node.label.startswith("Lightmap_"):
            created_nodes[mat.name] = node
            node.select = True
            nodes.active = node
            return node

    # If not found, create new image texture node
    image_node = nodes.new(type='ShaderNodeTexImage')
    image_node.label = f"Lightmap_{obj_name}"
    
    # Create new image
    image_name = f"Lightmap_{mat.name}"
    image = bpy.data.images.new(name=image_name, width=resolution, height=resolution)
    image.colorspace_settings.name = color_space
    
    image_node.image = image

    # Store the created node
    created_nodes[mat.name] = image_node

    # Select the new node and set it as active
    image_node.select = True
    nodes.active = image_node

    return image_node

def process_object(obj, material_usage, lightmap_settings):
    if obj.type != 'MESH' or obj.data is None:
        return

    # Store original UV state before any modifications
    store_original_uv_state(obj)

    make_single_user(obj)

    for mat_slot in obj.material_slots:
        if mat_slot.material is None:
            continue

        lightmap_uv = ensure_uv_maps(obj)
        if lightmap_uv is None:
            continue

        mat = mat_slot.material
        obj_count = material_usage.get(mat.name, 0)

        if obj_count < lightmap_settings['small_threshold']:
            resolution = lightmap_settings['resolution_single']
        elif obj_count < lightmap_settings['large_threshold']:
            resolution = lightmap_settings['resolution_small']
        else:
            resolution = lightmap_settings['resolution_large']

        find_or_create_image_texture(mat, obj.name, resolution, lightmap_settings['color_space'])

        # Add object to the list of objects sharing this material
        material_to_objects[mat.name].append(obj)

def unwrap_objects(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    # Set lightmap pack options
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.uv.select_all(action='SELECT')
    
    # Execute lightmap pack with available parameters
    bpy.ops.uv.lightmap_pack(
        PREF_CONTEXT='ALL_FACES',
        PREF_PACK_IN_ONE=True,
        PREF_NEW_UVLAYER=False,
        PREF_BOX_DIV=12,
        PREF_MARGIN_DIV=0.2
    )
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

def bake_objects(objects, bake_settings):
    # Select objects for baking
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    # Ensure we're in object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    scene = bpy.context.scene

    print("Blender bake settings before applying custom settings:")
    print(f"  bake_type: {scene.cycles.bake_type}")
    print(f"  use_pass_direct: {scene.render.bake.use_pass_direct}")
    print(f"  use_pass_indirect: {scene.render.bake.use_pass_indirect}")
    print(f"  use_pass_color: {scene.render.bake.use_pass_color}")
    print(f"  use_clear: {scene.render.bake.use_clear}")
    print(f"  use_adaptive_sampling: {scene.cycles.use_adaptive_sampling}")
    print(f"  adaptive_threshold: {scene.cycles.adaptive_threshold}")
    print(f"  samples: {scene.cycles.samples}")
    print(f"  adaptive_min_samples: {scene.cycles.adaptive_min_samples}")
    print(f"  use_denoising: {scene.cycles.use_denoising}")
    print(f"  denoiser: {scene.cycles.denoiser}")
    print(f"  denoising_input_passes: {scene.cycles.denoising_input_passes}")

    # Set up bake settings
    scene.cycles.bake_type = bake_settings['bake_type']
    scene.render.bake.use_pass_direct = bake_settings['use_pass_direct']
    scene.render.bake.use_pass_indirect = bake_settings['use_pass_indirect']
    scene.render.bake.use_pass_color = bake_settings['use_pass_color']
    scene.render.bake.use_clear = bake_settings['use_clear']
    scene.cycles.use_adaptive_sampling = bake_settings['use_adaptive_sampling']
    scene.cycles.adaptive_threshold = bake_settings['adaptive_threshold']
    scene.cycles.samples = bake_settings['samples']
    scene.cycles.adaptive_min_samples = bake_settings['adaptive_min_samples']
    scene.cycles.use_denoising = bake_settings['use_denoising']
    scene.cycles.denoiser = bake_settings['denoiser']
    scene.cycles.denoising_input_passes = bake_settings['denoising_input_passes']

    print("Blender bake settings after applying custom settings:")
    print(f"  bake_type: {scene.cycles.bake_type}")
    print(f"  use_pass_direct: {scene.render.bake.use_pass_direct}")
    print(f"  use_pass_indirect: {scene.render.bake.use_pass_indirect}")
    print(f"  use_pass_color: {scene.render.bake.use_pass_color}")
    print(f"  use_clear: {scene.render.bake.use_clear}")
    print(f"  use_adaptive_sampling: {scene.cycles.use_adaptive_sampling}")
    print(f"  adaptive_threshold: {scene.cycles.adaptive_threshold}")
    print(f"  samples: {scene.cycles.samples}")
    print(f"  adaptive_min_samples: {scene.cycles.adaptive_min_samples}")
    print(f"  use_denoising: {scene.cycles.use_denoising}")
    print(f"  denoiser: {scene.cycles.denoiser}")
    print(f"  denoising_input_passes: {scene.cycles.denoising_input_passes}")

    # Perform baking
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'})

    # Deselect objects after baking
    bpy.ops.object.select_all(action='DESELECT')

def process_and_bake_group(material_name, objects, bake_settings):
    print(f"Processing and baking group for material: {material_name}")
    unwrap_objects(objects)
    bake_objects(objects, bake_settings)
    print(f"Completed processing and baking for material: {material_name}")

def generate_lightmaps(objects, lightmap_settings, bake_settings):
    global created_nodes, material_to_objects, original_uv_states
    created_nodes = {}
    material_to_objects = defaultdict(list)
    original_uv_states = {}

    # Count material usage
    material_usage = {}
    for obj in objects:
        if obj.type == 'MESH' and obj.data is not None:
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    material_usage[mat_slot.material.name] = material_usage.get(mat_slot.material.name, 0) + 1

    # Process objects
    for obj in objects:
        process_object(obj, material_usage, lightmap_settings)

    # Unwrap and bake objects sharing the same material
    for material_name, material_objects in material_to_objects.items():
        process_and_bake_group(material_name, material_objects, bake_settings)

    # Restore original UV states
    restore_original_uv_states()

    print("Lightmap generation and baking completed. Original UV states restored.")

if __name__ == "__main__":
    # This part is for testing purposes only
    # In actual use, the generate_lightmaps function will be called from lightmap_operators.py
    from .lightmap_utils import get_lightmap_settings, get_bake_settings
    scene = bpy.context.scene
    visible_selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH' and not obj.hide_get()]
    lightmap_settings = get_lightmap_settings(scene)
    bake_settings = get_bake_settings(scene)
    generate_lightmaps(visible_selected_objects, lightmap_settings, bake_settings)