import bpy
import bmesh
import math
import time
import string
import random
from collections import defaultdict

def generate_random_string(length=16):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def ensure_cycles_render_engine():
    max_attempts = 5
    for attempt in range(max_attempts):
        print(f"Attempt {attempt + 1} to set render engine to Cycles")
        bpy.context.scene.render.engine = 'CYCLES'
        
        # Force Blender to update
        bpy.context.view_layer.update()
        
        # Give Blender a moment to update its internal state
        time.sleep(1)
        
        # Double-check that Cycles is set
        if bpy.context.scene.render.engine == 'CYCLES':
            print("Render engine is set to Cycles")
            
            # Ensure Cycles compute device is set (CPU or GPU)
            if bpy.context.preferences.addons['cycles'].preferences.compute_device_type == 'NONE':
                bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'  # or 'OPTIX' or 'HIP' depending on your GPU
            
            # Enable all available devices
            for device in bpy.context.preferences.addons['cycles'].preferences.devices:
                device.use = True
            
            return
    
    raise RuntimeError("Failed to set render engine to Cycles after multiple attempts. Please set it manually in Blender.")

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
        "render": next((uv.name for uv in mesh.uv_layers if uv.active_render), None),
        "uv_layers": [
            {
                "name": uv.name,
                "data": [uv_loop.uv.copy() for uv_loop in uv.data]
            } for uv in mesh.uv_layers
        ]
    }

def ensure_uv_maps(obj):
    mesh = obj.data
    
    # Check if there's an existing UV map in slot 0
    if len(mesh.uv_layers) > 0:
        first_uv = mesh.uv_layers[0]
        if first_uv.name != "UVMap":
            # Store the original UV map data and name
            original_uv_data = [uv_loop.uv.copy() for uv_loop in first_uv.data]
            original_uv_name = first_uv.name
            
            # Remove the existing UV map
            mesh.uv_layers.remove(first_uv)
            
            # Create a new "UVMap" in slot 0 with the original data
            new_uv = mesh.uv_layers.new(name="UVMap")
            for i, uv_loop in enumerate(new_uv.data):
                uv_loop.uv = original_uv_data[i]
    else:
        # If no UV maps exist, create "UVMap" in slot 0
        mesh.uv_layers.new(name="UVMap")
    
    # Check if "Lightmap" UV already exists
    lightmap_uv = next((uv for uv in mesh.uv_layers if uv.name == "Lightmap"), None)
    
    if lightmap_uv is None:
        # Create "Lightmap" UV in slot 1
        lightmap_uv = mesh.uv_layers.new(name="Lightmap")
    
    lightmap_uv.active = True
    lightmap_uv.active_render = True
    
    # Recreate the original UV map if it was replaced
    if 'original_uv_name' in locals() and original_uv_name != "UVMap":
        recreated_uv = mesh.uv_layers.new(name=original_uv_name)
        for i, uv_loop in enumerate(recreated_uv.data):
            uv_loop.uv = original_uv_data[i]
    
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
    print("Original UV states restored.")

def deselect_all_nodes(nodes):
    for node in nodes:
        node.select = False
    nodes.active = None

def find_or_create_image_texture(mat, width, height, color_space, shared_image=None, shared_label=None):
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
        if node.type == 'TEX_IMAGE' and node.label == shared_label:
            created_nodes[mat.name] = node
            node.select = True
            nodes.active = node
            return node

    # If not found, create new image texture node
    image_node = nodes.new(type='ShaderNodeTexImage')
    
    if shared_image and shared_label:
        image_node.label = shared_label
        image_node.image = shared_image
    else:
        # This case is for when automatic grouping is True
        random_string = generate_random_string()
        node_label = f"vircadia_lightmapData_{random_string}"
        image_node.label = node_label
        image = bpy.data.images.new(name=node_label, width=width, height=height)
        image.colorspace_settings.name = color_space
        image_node.image = image

    # Store the created node
    created_nodes[mat.name] = image_node

    # Select the new node and set it as active
    image_node.select = True
    nodes.active = image_node

    return image_node

def find_or_create_shared_image_texture(objects, lightmap_settings, width, height):
    # Check if any object already has a Lightmap texture
    for obj in objects:
        for mat_slot in obj.material_slots:
            if mat_slot.material:
                nodes = mat_slot.material.node_tree.nodes
                for node in nodes:
                    if node.type == 'TEX_IMAGE' and node.label.startswith("Lightmap_"):
                        return node.image

    # If no existing Lightmap texture found, create a new one
    image_name = f"Lightmap_Grouped"
    shared_image = bpy.data.images.new(name=image_name, width=width, height=height)
    shared_image.colorspace_settings.name = lightmap_settings['color_space']
    return shared_image

def calculate_object_surface_area(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    area = sum(f.calc_area() for f in bm.faces)
    bm.free()
    print(f"Surface area for object {obj.name}: {area}")
    return area

def determine_lightmap_resolution(surface_area, lightmap_settings, obj):
    texel_density = lightmap_settings['texel_density']
    min_resolution = lightmap_settings['min_resolution']
    max_resolution = lightmap_settings['max_resolution']

    # Calculate the required resolution based on surface area and texel density
    total_texels = surface_area * texel_density
    base_resolution = math.sqrt(total_texels)
    
    # Scale the resolution to ensure larger objects get larger textures
    scaled_resolution = base_resolution * math.log2(base_resolution)
    
    # Round to the nearest power of two
    resolution = 2 ** math.ceil(math.log2(scaled_resolution))
    
    # Clamp the resolution between min and max
    final_resolution = max(min_resolution, min(resolution, max_resolution))
    
    # For grouped objects, we might want to increase the resolution
    if not lightmap_settings['automatic_grouping']:
        final_resolution *= 2  # You can adjust this factor as needed
    
    # Determine aspect ratio based on object's bounding box
    bbox = obj.bound_box
    width = max(bbox[i][0] for i in range(8)) - min(bbox[i][0] for i in range(8))
    height = max(bbox[i][1] for i in range(8)) - min(bbox[i][1] for i in range(8))
    
    if width > height * 1.5:
        return final_resolution * 2, final_resolution
    elif height > width * 1.5:
        return final_resolution, final_resolution * 2
    else:
        return final_resolution, final_resolution

    print(f"Final resolution: {final_resolution}x{final_resolution}")

def process_object(obj, lightmap_settings):
    if obj.type != 'MESH' or obj.data is None:
        return

    make_single_user(obj)

    surface_area = calculate_object_surface_area(obj)
    width, height = determine_lightmap_resolution(surface_area, lightmap_settings, obj)

    for mat_slot in obj.material_slots:
        if mat_slot.material is None:
            continue

        lightmap_uv = ensure_uv_maps(obj)
        if lightmap_uv is None:
            continue

        mat = mat_slot.material
        find_or_create_image_texture(mat, width, height, lightmap_settings['color_space'])

        # Add object to the list of objects sharing this material
        material_to_objects[mat.name].append(obj)
        
def process_grouped_objects(objects, lightmap_settings):
    # Calculate total surface area for all objects
    total_surface_area = sum(calculate_object_surface_area(obj) for obj in objects)
    
    # Determine shared lightmap resolution
    width, height = determine_lightmap_resolution(total_surface_area, lightmap_settings, objects[0])
    
    # Create a shared image for all objects
    random_string = generate_random_string()
    shared_image_name = f"vircadia_lightmapData_{random_string}"
    shared_image = bpy.data.images.new(name=shared_image_name, width=width, height=height)
    shared_image.colorspace_settings.name = lightmap_settings['color_space']
    
    # Create a shared label for all image texture nodes
    shared_label = shared_image_name
    
    for obj in objects:
        make_single_user(obj)
        lightmap_uv = ensure_uv_maps(obj)
        
        for mat_slot in obj.material_slots:
            if mat_slot.material is None:
                continue
            
            mat = mat_slot.material
            image_node = find_or_create_image_texture(mat, width, height, lightmap_settings['color_space'], shared_image, shared_label)

    return shared_label  # Return the shared label for potential use elsewhere

def unwrap_objects(objects, lightmap_settings):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    # Set lightmap pack options
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    bpy.ops.uv.select_all(action='SELECT')
    
    # Execute the selected UV unwrapping method
    uv_type = lightmap_settings['uv_type']
    
    if uv_type == 'LIGHTMAP_PACK':
        bpy.ops.uv.lightmap_pack(
            PREF_CONTEXT=lightmap_settings['unwrap_context'],
            PREF_PACK_IN_ONE=True,
            PREF_NEW_UVLAYER=False,
            PREF_BOX_DIV=12,
            PREF_MARGIN_DIV=lightmap_settings['margin']
        )
    elif uv_type == 'SMART_UV_PROJECT':
        bpy.ops.uv.smart_project(
            angle_limit=66.0,
            island_margin=lightmap_settings['margin'],
            area_weight=1.0,
            correct_aspect=True,
            scale_to_bounds=False
        )
    elif uv_type == 'UNWRAP':
        bpy.ops.uv.unwrap(
            method='ANGLE_BASED',
            margin=lightmap_settings['margin']
        )
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

def bake_objects(objects, bake_settings):
    # Ensure we're using Cycles
    ensure_cycles_render_engine()

    # Select objects for baking
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    # Ensure we're in object mode
    bpy.ops.object.mode_set(mode='OBJECT')

    scene = bpy.context.scene

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
    scene.render.bake.margin = bake_settings['bake_margin']

    # Perform baking
    try:
        bpy.ops.object.bake(type='DIFFUSE', pass_filter={'DIRECT', 'INDIRECT'})
    except RuntimeError as e:
        print(f"Baking failed: {str(e)}")
        print(f"Current render engine: {bpy.context.scene.render.engine}")
        print(f"Cycles compute device type: {bpy.context.preferences.addons['cycles'].preferences.compute_device_type}")
        print(f"Enabled devices: {[device.name for device in bpy.context.preferences.addons['cycles'].preferences.devices if device.use]}")
        raise

    # Deselect objects after baking
    bpy.ops.object.select_all(action='DESELECT')

import bpy
from collections import defaultdict

def generate_lightmaps(objects, lightmap_settings, bake_settings):
    ensure_cycles_render_engine()
    
    global created_nodes, material_to_objects, original_uv_states
    created_nodes = {}
    material_to_objects = defaultdict(list)
    original_uv_states = {}
    created_lightmap_textures = []

    # Store original UV states at the very beginning
    for obj in objects:
        if obj.type == 'MESH':
            store_original_uv_state(obj)

    try:
        if lightmap_settings['automatic_grouping']:
            # Existing logic for automatic grouping
            for obj in objects:
                process_object(obj, lightmap_settings)

            for material_name, material_objects in material_to_objects.items():
                if lightmap_settings['factor_shared_materials']:
                    all_objects_with_material = [obj for obj in bpy.data.objects if obj.type == 'MESH' and any(slot.material and slot.material.name == material_name for slot in obj.material_slots)]
                    unwrap_objects(all_objects_with_material, lightmap_settings)
                    bake_objects(all_objects_with_material, bake_settings)
                else:
                    unwrap_objects(material_objects, lightmap_settings)
                    bake_objects(material_objects, bake_settings)
        else:
            # Logic for manual grouping
            process_grouped_objects(objects, lightmap_settings)
            unwrap_objects(objects, lightmap_settings)
            bake_objects(objects, bake_settings)

        # Collect all created lightmap textures
        for node in created_nodes.values():
            if node.image and node.image.name.startswith("vircadia_lightmapData_"):
                created_lightmap_textures.append(node.image)

        # Create materials for lightmap textures
        create_lightmap_materials(created_lightmap_textures)

        # Add correct custom properties to original objects
        for obj in objects:
            if obj.type == 'MESH':
                for material_slot in obj.material_slots:
                    if material_slot.material and material_slot.material.name in created_nodes:
                        lightmap_node = created_nodes[material_slot.material.name]
                        if lightmap_node.image:
                            # Extract the 16-digit string from the lightmap name
                            lightmap_id = lightmap_node.image.name.split("_")[2]
                            obj['vircadia_lightmap'] = f"vircadia_lightmapData_{lightmap_id}"
                            obj['vircadia_lightmap_texcoord'] = 1
                            break  # Only need to set these properties once per object

    except Exception as e:
        print(f"An error occurred during lightmap generation: {str(e)}")
    finally:
        # Restore original UV states
        restore_original_uv_states()

    print("Lightmap generation and baking completed. Original UV states restored and correct custom properties added.")

def create_lightmap_materials(lightmap_textures):
    # Ensure the vircadia_lightmapData collection exists
    lightmap_collection = bpy.data.collections.get("vircadia_lightmapData")
    if not lightmap_collection:
        lightmap_collection = bpy.data.collections.new("vircadia_lightmapData")
        bpy.context.scene.collection.children.link(lightmap_collection)

    # Check if vircadia_lightmapData object already exists
    existing_lightmap_obj = bpy.data.objects.get("vircadia_lightmapData")

    # Create a new object for the new lightmap data
    new_mesh = bpy.data.meshes.new("new_lightmap_data_mesh")
    new_lightmap_obj = bpy.data.objects.new("new_lightmap_data", new_mesh)
    lightmap_collection.objects.link(new_lightmap_obj)

    # Create a dictionary to group textures by their label
    texture_groups = {}
    for texture in lightmap_textures:
        label = texture.name.split("_")[2]  # Assuming the format is "vircadia_lightmapData_XXXXXXXXXXXXXXXX"
        if label not in texture_groups:
            texture_groups[label] = texture

    # Create a bmesh to build the mesh
    bm = bmesh.new()

    for label, texture in texture_groups.items():
        # Create a new plane in the bmesh
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1)

        # Create material for the texture
        material_name = f"vircadia_lightmapData_{label}"
        mat = bpy.data.materials.new(name=material_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create Principled BSDF node
        principled_node = nodes.new(type='ShaderNodeBsdfPrincipled')
        principled_node.location = (0, 0)

        # Create Image Texture node
        tex_node = nodes.new(type='ShaderNodeTexImage')
        tex_node.location = (-300, 0)
        tex_node.image = texture

        # Create Material Output node
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (300, 0)

        # Link nodes
        links.new(tex_node.outputs['Color'], principled_node.inputs['Base Color'])
        links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])

        # Assign material to the new_lightmap_obj
        new_lightmap_obj.data.materials.append(mat)

        # Assign the material index to the faces of this plane
        for face in bm.faces[-4:]:  # Last 4 faces correspond to the plane we just created
            face.material_index = len(new_lightmap_obj.data.materials) - 1

    # Update the mesh with bmesh data
    bm.to_mesh(new_lightmap_obj.data)
    bm.free()

    # Update mesh to reflect changes
    new_lightmap_obj.data.update()

    final_lightmap_obj = None

    if existing_lightmap_obj:
        # If vircadia_lightmapData already exists, merge the new object into it
        bpy.ops.object.select_all(action='DESELECT')
        new_lightmap_obj.select_set(True)
        existing_lightmap_obj.select_set(True)
        bpy.context.view_layer.objects.active = existing_lightmap_obj  # Set the existing object as active
        bpy.ops.object.join()
        final_lightmap_obj = existing_lightmap_obj
        print(f"Merged new lightmap data into existing vircadia_lightmapData object.")
    else:
        # If vircadia_lightmapData doesn't exist, rename the new object
        new_lightmap_obj.name = "vircadia_lightmapData"
        final_lightmap_obj = new_lightmap_obj
        print(f"Created new vircadia_lightmapData object.")

    # Add the custom property after joining or renaming
    final_lightmap_obj["vircadia_lightmap_mode"] = "shadowsOnly"

    print(f"Updated vircadia_lightmapData object with {len(texture_groups)} new unique lightmap materials.")
    print(f"Added custom property 'vircadia_lightmap_mode' with value 'shadowsOnly' to the final object.")

if __name__ == "__main__":
    # This part is for testing purposes only
    # In actual use, the generate_lightmaps function will be called from lightmap_operators.py
    from .lightmap_utils import get_lightmap_settings, get_bake_settings
    scene = bpy.context.scene
    visible_selected_objects = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH' and not obj.hide_get()]
    lightmap_settings = get_lightmap_settings(scene)
    bake_settings = get_bake_settings(scene)
    generate_lightmaps(visible_selected_objects, lightmap_settings, bake_settings)