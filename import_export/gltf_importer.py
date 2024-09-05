import bpy
import os
from mathutils import Matrix

def find_matching_object(filename):
    for obj in bpy.data.objects:
        if obj.get("modelURL") and filename in obj["modelURL"]:
            return obj
    return None

def import_gltf_or_glb(context, filepaths):
    original_selection = context.selected_objects.copy()
    original_active = context.active_object

    for filepath in filepaths:
        if not os.path.exists(filepath):
            print(f"Error: File {filepath} does not exist.")
            continue

        file_ext = os.path.splitext(filepath)[1].lower()
        if file_ext not in ['.gltf', '.glb']:
            print(f"Error: Unsupported file format. Expected .gltf or .glb, got {file_ext}")
            continue

        filename = os.path.basename(filepath)
        matching_obj = find_matching_object(filename)

        # Store the current selection before importing
        pre_import_selection = context.selected_objects.copy()

        # Import the GLTF/GLB file
        try:
            bpy.ops.import_scene.gltf(
                filepath=filepath,
                import_pack_images=True,
                merge_vertices=False,
                import_shading='NORMALS',
                bone_heuristic='BLENDER',
                guess_original_bind_pose=True
            )
            print(f"Successfully imported GLTF from {filepath}")
        except Exception as e:
            print(f"Error importing GLTF: {str(e)}")
            continue

        # Get the newly imported objects for this specific GLB
        new_objects = [obj for obj in context.selected_objects if obj not in pre_import_selection]

        if matching_obj:
            # Calculate the offset
            offset = matching_obj.matrix_world.to_translation()

            # Parent all imported objects to the matching object and adjust their positions
            for obj in new_objects:
                # Store the original world matrix
                original_matrix = obj.matrix_world.copy()
                
                # Set the parent
                obj.parent = matching_obj
                
                # Reset the parent inverse to identity
                obj.matrix_parent_inverse = matching_obj.matrix_world.inverted()
                
                # Set the object's matrix_world to its original value
                obj.matrix_world = original_matrix
                
                # Apply only the position offset
                obj.location += offset

                # Remove the object from all collections except the parent's collection
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                
                # Ensure the object is in the parent's collection
                parent_collections = matching_obj.users_collection
                if parent_collections:
                    parent_collections[0].objects.link(obj)

                # Apply visibility settings
                update_object_visibility(obj, context.scene)

            print(f"Parented {len(new_objects)} objects to {matching_obj.name}")
        else:
            print(f"No matching object found for {filename}. Importing at scene origin.")
            for obj in new_objects:
                update_object_visibility(obj, context.scene)

        # Update the original_selection to include the new objects
        original_selection.extend(new_objects)

    # Restore original selection and active object
    bpy.ops.object.select_all(action='DESELECT')
    for obj in original_selection:
        obj.select_set(True)
    if original_active:
        context.view_layer.objects.active = original_active

    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

    print("GLTF import completed.")

def update_object_visibility(obj, scene):
    # Check if object is a collision object
    is_collision = any(name in obj.name.lower() for name in ["collision", "collider", "collides"]) or \
                   (obj.parent and any(name in obj.parent.name.lower() for name in ["collision", "collider", "collides"]))

    # Check if object is an LOD level (except LOD0)
    is_lod = any(f"_LOD{i}" in obj.name for i in range(1, 100))  # Checking up to LOD99

    # Update visibility based on settings
    if is_collision:
        obj.hide_viewport = scene.vircadia_hide_collisions
        obj.display_type = 'WIRE' if scene.vircadia_collisions_wireframe else 'TEXTURED'
    elif is_lod:
        obj.hide_viewport = scene.vircadia_hide_lod_levels
    elif obj.type == 'ARMATURE':
        obj.hide_viewport = scene.vircadia_hide_armatures

    # Apply settings to children recursively
    for child in obj.children:
        update_object_visibility(child, scene)

def register():
    pass

def unregister():
    pass
