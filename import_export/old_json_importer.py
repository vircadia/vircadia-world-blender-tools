import bpy
import json
import os
from ..utils import coordinate_utils, property_utils, world_setup, object_creation, collection_utils, error_handling

def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except PermissionError:
        error_handling.log_error(f"Permission denied when trying to read {file_path}")
    except FileNotFoundError:
        error_handling.log_error(f"File not found: {file_path}")
    except json.JSONDecodeError:
        error_handling.log_error(f"Invalid JSON file: {file_path}")
    return None

def import_entities(data, json_directory):
    zone_objs = []
    for entity in data.get("Entities", []):
        # Ensure "type" has only the first letter capitalized
        if "type" in entity:
            entity["type"] = entity["type"].title()
        
        # Ensure "shape" has only the first letter capitalized if it exists
        if "shape" in entity:
            entity["shape"] = entity["shape"].title()

        obj = object_creation.create_blender_object(entity)
        if obj is not None:
            # Special handling for zone objects
            if entity.get("type") == "Zone":
                base_name = "Zone"
                unique_name = base_name
                counter = 1
                while unique_name in bpy.data.objects:
                    unique_name = f"{base_name}.{counter:03d}"
                    counter += 1
                obj.name = unique_name
                obj["name"] = unique_name
                zone_objs.append(obj)
                # Set display type to wireframe for zones
                obj.display_type = 'WIRE'
            
            # Set custom properties
            property_utils.set_custom_properties(obj, entity)
            
            # Additional check to ensure zone objects always have their unique name as their name custom property
            if obj.get("type") == "Zone":
                obj["name"] = obj.name

            # Move the object to the appropriate collection
            zone_collection = move_to_type_collection(obj, entity.get("type", "Unknown"))
            
            # Add transform update handler
            bpy.app.handlers.depsgraph_update_post.append(object_creation.create_transform_update_handler(obj))

        else:
            error_handling.log_import_error(entity)
    return zone_objs

def move_to_type_collection(obj, entity_type):
    # Get or create the collection for this entity type
    collection = collection_utils.get_or_create_collection(entity_type)
    
    # Remove the object from all other collections
    for coll in obj.users_collection:
        coll.objects.unlink(obj)
    
    # Link the object to the type-specific collection
    collection.objects.link(obj)
    
    return collection

def process_vircadia_json(file_path):
    data = load_json(file_path)
    if data is None:
        return

    json_directory = os.path.dirname(os.path.normpath(file_path))
    zone_objs = import_entities(data, json_directory)

    for zone_obj in zone_objs:
        world_setup.setup_hdri_and_skybox(zone_obj, json_directory)
        # Get the zone collection
        zone_collection = zone_obj.users_collection[0]
        world_setup.setup_sun_light(zone_obj, zone_collection)

    if not zone_objs:
        error_handling.log_warning("No zone entity found in the imported data.")

    world_setup.configure_world_and_viewport()
    
    # Clean up empty collections
    collection_utils.remove_empty_collections()
    
    print("Vircadia entities imported successfully.")

def register():
    pass

def unregister():
    pass