import bpy
import bmesh
from collections import defaultdict
from .lightmap_utils import (
    COLOR_SPACE,
    RESOLUTION_SINGLE,
    RESOLUTION_SMALL_GROUP,
    RESOLUTION_LARGE_GROUP,
    SMALL_GROUP_THRESHOLD,
    LARGE_GROUP_THRESHOLD,
    setup_bake_settings
)

# Dictionary to store created image texture nodes
created_nodes = {}

# Dictionary to store objects sharing the same material
material_to_objects = defaultdict(list)

def make_single_user(obj):
    if obj.data.users > 1:
        new_mesh = obj.data.copy()
        obj.data = new_mesh

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

def deselect_all_nodes(nodes):
    for node in nodes:
        node.select = False
    nodes.active = None

def find_or_create_image_texture(mat, obj_name, resolution):
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
    image.colorspace_settings.name = COLOR_SPACE
    
    image_node.image = image

    # Store the created node
    created_nodes[mat.name] = image_node

    # Select the new node and set it as active
    image_node.select = True
    nodes.active = image_node

    return image_node

def process_object(obj, material_usage):
    if obj.type != 'MESH' or obj.data is None:
        return

    make_single_user(obj)

    for mat_slot in obj.material_slots:
        if mat_slot.material is None:
            continue

        lightmap_uv = ensure_uv_maps(obj)
        if lightmap_uv is None:
            continue

        mat = mat_slot.material
        obj_count = material_usage.get(mat.name, 0)

        if obj_count < SMALL_GROUP_THRESHOLD:
            resolution = RESOLUTION_SINGLE
        elif obj_count < LARGE_GROUP_THRESHOLD:
            resolution = RESOLUTION_SMALL_GROUP
        else:
            resolution = RESOLUTION_LARGE_GROUP

        find_or_create_image_texture(mat, obj.name, resolution)

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

def bake_objects(objects):
    # Select objects for baking
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    # Ensure we're in object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    # Perform baking
    bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'})

    # Deselect objects after baking
    bpy.ops.object.select_all(action='DESELECT')

def process_and_bake_group(material_name, objects):
    print(f"Processing and baking group for material: {material_name}")
    unwrap_objects(objects)
    bake_objects(objects)
    print(f"Completed processing and baking for material: {material_name}")

def generate_lightmaps():
    global created_nodes, material_to_objects
    created_nodes = {}
    material_to_objects = defaultdict(list)

    # Set up bake settings
    setup_bake_settings()

    # Count material usage
    material_usage = {}
    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH' and obj.data is not None:
            for mat_slot in obj.material_slots:
                if mat_slot.material:
                    material_usage[mat_slot.material.name] = material_usage.get(mat_slot.material.name, 0) + 1

    # Process objects
    for obj in bpy.context.selected_objects:
        process_object(obj, material_usage)

    # Unwrap and bake objects sharing the same material
    for material_name, objects in material_to_objects.items():
        process_and_bake_group(material_name, objects)

    print("Lightmap generation and baking completed.")

if __name__ == "__main__":
    generate_lightmaps()
