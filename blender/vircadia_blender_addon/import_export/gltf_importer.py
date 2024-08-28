import bpy
import os
from mathutils import Vector

def find_matching_object(filename):
    for obj in bpy.data.objects:
        if obj.get("modelURL") and filename in obj["modelURL"]:
            return obj
    return None

def import_gltf(context, filepaths):
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

        # Import the GLTF/GLB file using built-in importer with default settings
        try:
            bpy.ops.import_scene.gltf(filepath=filepath)
            print(f"Successfully imported GLTF from {filepath}")
        except Exception as e:
            print(f"Error importing GLTF: {str(e)}")
            continue

        # Get the newly imported objects for this specific GLB
        new_objects = [obj for obj in context.selected_objects if obj not in pre_import_selection]

        if matching_obj:
            # Calculate the offset
            offset = matching_obj.location

            # Parent all imported objects to the matching object and adjust their positions
            for obj in new_objects:
                original_location = obj.location.copy()
                obj.parent = matching_obj
                # Set the object's location relative to the parent
                obj.location = original_location

            print(f"Parented {len(new_objects)} objects to {matching_obj.name}")
        else:
            print(f"No matching object found for {filename}. Importing at scene origin.")

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

def register():
    pass

def unregister():
    pass
