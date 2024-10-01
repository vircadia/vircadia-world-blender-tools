import bpy

def update_visibility(scene, context):
    for obj in bpy.data.objects:
        update_object_visibility(obj, scene)

def update_object_visibility(obj, scene):
    # Check if object is a collision object
    is_collision = any(name in obj.name.lower() for name in ["collision", "collider", "collides", "collisions", "colliders"])

    # Check if object is an LOD level (except LOD0)
    is_lod = any(f"_LOD{i}" in obj.name for i in range(1, 100))  # Checking up to LOD99

    # Update visibility based on settings
    if is_collision:
        obj.hide_set(scene.vircadia_hide_collisions)
    elif is_lod:
        obj.hide_set(scene.vircadia_hide_lod_levels)

def temporarily_unhide_objects(context):
    hidden_objects = []
    print("Temporarily unhiding objects")
    for obj in bpy.data.objects:
        visibility_state = {
            'hide_viewport': obj.hide_viewport,
            'hide_render': obj.hide_render,
            'hide_get': obj.hide_get(),
            'display_type': obj.display_type
        }
        if any(visibility_state.values()):
            hidden_objects.append((obj, visibility_state))
            obj.hide_viewport = False
            obj.hide_render = False
            obj.hide_set(False)
            obj.display_type = 'TEXTURED'
    print(f"Temporarily unhidden {len(hidden_objects)} objects")
    return hidden_objects

def restore_hidden_objects(hidden_objects):
    print("Restoring hidden objects")
    for obj, visibility_state in hidden_objects:
        obj.hide_viewport = visibility_state['hide_viewport']
        obj.hide_render = visibility_state['hide_render']
        obj.hide_set(visibility_state['hide_get'])
        obj.display_type = visibility_state['display_type']
    print(f"Restored {len(hidden_objects)} hidden objects")