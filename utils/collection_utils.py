import bpy

def get_or_create_collection(name):
    # Ensure the name has only the first letter capitalized
    name = name.title()
    
    # Check if a collection with this name (case-insensitive) already exists
    for collection in bpy.data.collections:
        if collection.name.lower() == name.lower():
            # If it exists but with different capitalization, rename it
            if collection.name != name:
                collection.name = name
            return collection
    
    # If no matching collection is found, create a new one
    new_collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(new_collection)
    return new_collection

def remove_empty_collections():
    for collection in bpy.data.collections:
        if len(collection.objects) == 0 and collection.name != "Scene Collection":
            bpy.data.collections.remove(collection)