import bpy

def temporarily_unhide_objects(context):
    hidden_objects = []
    print("Temporarily unhiding objects")
    for obj in bpy.data.objects:
        if obj.hide_viewport:
            hidden_objects.append(obj)
            obj.hide_viewport = False
    print("Temporarily unhidden objects ", hidden_objects)
    return hidden_objects

def restore_hidden_objects(hidden_objects):
    print("Restoring hidden objects")
    for obj in hidden_objects:
        obj.hide_viewport = True
    print("Restored hidden objects ", hidden_objects)
