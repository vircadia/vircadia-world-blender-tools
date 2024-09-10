import bpy
from bpy.types import Panel, Operator
from bpy.props import BoolProperty, StringProperty

def update_visibility(self, context):
    for obj in bpy.data.objects:
        update_object_visibility(obj, context.scene)

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

class VIRCADIA_OT_paste_content_path(Operator):
    bl_idname = "vircadia.paste_content_path"
    bl_label = "Paste"
    bl_description = "Paste content path from clipboard"

    def execute(self, context):
        context.scene.vircadia_content_path = bpy.context.window_manager.clipboard
        return {'FINISHED'}

class VIRCADIA_OT_convert_collisions(Operator):
    bl_idname = "vircadia.convert_collisions"
    bl_label = "Convert Collisions To Vircadia"
    bl_description = "Convert collision objects to Vircadia entities and move them to a Colliders collection"

    def execute(self, context):
        # Store the original collision visibility state
        original_hide_collisions = context.scene.vircadia_hide_collisions

        # Temporarily unhide collisions
        context.scene.vircadia_hide_collisions = False
        update_visibility(self, context)

        # Create or get the "Colliders" collection
        colliders_collection = bpy.data.collections.get("Colliders")
        if colliders_collection is None:
            colliders_collection = bpy.data.collections.new("Colliders")
            context.scene.collection.children.link(colliders_collection)

        # Process all objects
        converted_count = 0
        for obj in bpy.data.objects:
            if any(name in obj.name.lower() for name in ["collision", "collider", "collides", "collisions", "colliders"]):
                obj["vircadia_collider"] = 0
                converted_count += 1

                # Move the object to the Colliders collection
                for coll in obj.users_collection:
                    coll.objects.unlink(obj)
                colliders_collection.objects.link(obj)

        # Restore original collision visibility state
        context.scene.vircadia_hide_collisions = original_hide_collisions
        update_visibility(self, context)

        self.report({'INFO'}, f"Converted {converted_count} collision objects to Vircadia entities and moved them to the Colliders collection.")
        return {'FINISHED'}

class VIRCADIA_OT_process_lod(Operator):
    bl_idname = "vircadia.process_lod"
    bl_label = "Process LOD Objects"
    bl_description = "Process LOD objects and add distance properties"

    def execute(self, context):
        # Store the original LOD visibility state
        original_hide_lod = context.scene.vircadia_hide_lod_levels

        # Temporarily unhide LOD levels
        context.scene.vircadia_hide_lod_levels = False
        update_visibility(self, context)

        processed_count = 0
        existing_property_count = 0

        for obj in bpy.data.objects:
            if "_LOD" in obj.name:
                lod_level = int(obj.name.split("_LOD")[-1])
                if lod_level > 0:
                    property_name = "vircadia_lod_distance"
                    if property_name not in obj:
                        obj[property_name] = lod_level * 32
                        processed_count += 1
                    else:
                        existing_property_count += 1

        # Restore original LOD visibility state
        context.scene.vircadia_hide_lod_levels = original_hide_lod
        update_visibility(self, context)

        self.report({'INFO'}, f"Processed {processed_count} LOD objects. {existing_property_count} objects already had the property.")
        return {'FINISHED'}

class VIRCADIA_PT_main_panel(Panel):
    bl_label = "World Properties"
    bl_idname = "VIEW3D_PT_vircadia_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vircadia"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Import/Export Section
        box = layout.box()
        box.label(text="Import/Export")

        # Import Sub-Section
        import_box = box.box()
        import_box.label(text="Import")
        row = import_box.row()
        row.operator("import_scene.vircadia_json", text="Import JSON")
        row.operator("import_scene.vircadia_gltf", text="Import GLTF")

        # Export Sub-Section
        export_box = box.box()
        export_box.label(text="Export")

        # Content Path
        row = export_box.row(align=True)
        row.prop(scene, "vircadia_content_path", text="Content Path")
        row.operator("vircadia.paste_content_path", text="", icon='PASTEDOWN')

        row = export_box.row()
        row.operator("export_scene.vircadia_json", text="Export JSON")
        row.operator("export_scene.vircadia_glb", text="Export GLB")

        # Convert Collisions
        box.operator("vircadia.convert_collisions", text="Convert Collisions To Vircadia")

        # Process LOD Objects
        box.operator("vircadia.process_lod", text="Process LOD Objects")

        # Visibility toggles
        box = layout.box()
        box.label(text="Visibility Options")
        box.prop(scene, "vircadia_hide_collisions", text="Hide Collisions")
        box.prop(scene, "vircadia_collisions_wireframe", text="Collisions as Wireframe")
        box.prop(scene, "vircadia_hide_lod_levels", text="Hide LOD Levels")
        box.prop(scene, "vircadia_hide_armatures", text="Hide Armatures")

def register():
    bpy.utils.register_class(VIRCADIA_OT_paste_content_path)
    bpy.utils.register_class(VIRCADIA_OT_convert_collisions)
    bpy.utils.register_class(VIRCADIA_OT_process_lod)
    bpy.types.Scene.vircadia_content_path = StringProperty(
        name="Content Path",
        description="Path to the content directory for Vircadia assets",
        default="",
    )
    bpy.types.Scene.vircadia_hide_collisions = BoolProperty(
        name="Hide Collisions",
        description="Hide collision objects",
        default=True,
        update=update_visibility
    )
    bpy.types.Scene.vircadia_collisions_wireframe = BoolProperty(
        name="Collisions as Wireframe",
        description="Display collision objects as wireframe",
        default=False,
        update=update_visibility
    )
    bpy.types.Scene.vircadia_hide_lod_levels = BoolProperty(
        name="Hide LOD Levels",
        description="Hide LOD levels except LOD0",
        default=True,
        update=update_visibility
    )
    bpy.types.Scene.vircadia_hide_armatures = BoolProperty(
        name="Hide Armatures",
        description="Hide armatures",
        default=True,
        update=update_visibility
    )
    bpy.utils.register_class(VIRCADIA_PT_main_panel)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_PT_main_panel)
    bpy.utils.unregister_class(VIRCADIA_OT_process_lod)
    bpy.utils.unregister_class(VIRCADIA_OT_convert_collisions)
    bpy.utils.unregister_class(VIRCADIA_OT_paste_content_path)
    del bpy.types.Scene.vircadia_hide_collisions
    del bpy.types.Scene.vircadia_collisions_wireframe
    del bpy.types.Scene.vircadia_hide_lod_levels
    del bpy.types.Scene.vircadia_hide_armatures
    del bpy.types.Scene.vircadia_content_path

if __name__ == "__main__":
    register()