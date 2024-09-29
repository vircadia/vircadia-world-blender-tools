import bpy
import json
import os
import logging
from ..utils import coordinate_utils, object_utils, property_utils, world_setup, collection_utils, error_handling

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
        logging.info(f"Processing entity: {entity.get('name', 'Unnamed')} (Type: {entity.get('type', 'Unknown')})")
        
        # Ensure "type" has only the first letter capitalized
        if "type" in entity:
            entity["type"] = entity["type"].title()
        
        # Ensure "shape" has only the first letter capitalized if it exists
        if "shape" in entity:
            entity["shape"] = entity["shape"].title()
        
        # Handle legacy "box" shape
        if entity.get("shape") == "Box":
            entity["shape"] = "Shape"

        try:
            obj = object_utils.create_blender_object(entity)
            if obj is not None:
                logging.info(f"Created Blender object: {obj.name}")
                
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
                
                # Set initial properties
                try:
                    property_utils.set_initial_properties(obj, entity)
                    logging.info(f"Set initial properties for {obj.name}")
                except Exception as prop_error:
                    logging.error(f"Error setting properties for {obj.name}: {str(prop_error)}")
                
                # Additional check to ensure zone objects always have their unique name as their name custom property
                if obj.get("type") == "Zone":
                    obj["name"] = obj.name

                # Move the object to the appropriate collection
                try:
                    zone_collection = move_to_type_collection(obj, entity.get("type", "Unknown"))
                    logging.info(f"Moved {obj.name} to collection {zone_collection.name}")
                except Exception as coll_error:
                    logging.error(f"Error moving {obj.name} to collection: {str(coll_error)}")

            else:
                logging.warning(f"Failed to create object for entity: {entity.get('name', 'Unnamed')}")
        except Exception as obj_error:
            logging.error(f"Error creating object for entity {entity.get('name', 'Unnamed')}: {str(obj_error)}")
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
    logging.info(f"Starting to process Vircadia JSON: {file_path}")
    data = load_json(file_path)
    if data is None:
        logging.error("Failed to load JSON data")
        return

    json_directory = os.path.dirname(os.path.normpath(file_path))
    logging.info(f"JSON directory: {json_directory}")

    zone_objs = import_entities(data, json_directory)
    logging.info(f"Imported {len(zone_objs)} zone objects")

    for zone_obj in zone_objs:
        try:
            world_setup.setup_hdri_and_skybox(zone_obj, json_directory)
            logging.info(f"Set up HDRI and skybox for zone: {zone_obj.name}")
            # Get the zone collection
            zone_collection = zone_obj.users_collection[0]
            world_setup.setup_sun_light(zone_obj, zone_collection)
            logging.info(f"Set up sun light for zone: {zone_obj.name}")
        except Exception as zone_error:
            logging.error(f"Error setting up zone {zone_obj.name}: {str(zone_error)}")

    if not zone_objs:
        logging.warning("No zone entity found in the imported data.")

    try:
        world_setup.configure_world_and_viewport()
        logging.info("Configured world and viewport")
    except Exception as world_error:
        logging.error(f"Error configuring world and viewport: {str(world_error)}")
    
    # Clean up empty collections
    try:
        collection_utils.remove_empty_collections()
        logging.info("Removed empty collections")
    except Exception as cleanup_error:
        logging.error(f"Error cleaning up collections: {str(cleanup_error)}")
    
    logging.info("Vircadia entities import process completed")

def register():
    pass

def unregister():
    pass