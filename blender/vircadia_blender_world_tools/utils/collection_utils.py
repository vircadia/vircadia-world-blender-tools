import bpy

def get_or_create_collection(name):
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    else:
        new_collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(new_collection)
        return new_collection
