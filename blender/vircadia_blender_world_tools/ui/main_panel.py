import bpy
from bpy.types import Panel
from bpy.props import BoolProperty

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

class VIRCADIA_PT_main_panel(Panel):
    bl_label = "Vircadia"
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
        row = export_box.row()
        row.operator("export_scene.vircadia_json", text="Export JSON")
        row.operator("export_scene.vircadia_gltf", text="Export GLTF")

        # Visibility toggles
        box = layout.box()
        box.label(text="Visibility Options")
        box.prop(scene, "vircadia_hide_collisions", text="Hide Collisions")
        box.prop(scene, "vircadia_collisions_wireframe", text="Collisions as Wireframe")
        box.prop(scene, "vircadia_hide_lod_levels", text="Hide LOD Levels")
        box.prop(scene, "vircadia_hide_armatures", text="Hide Armatures")

def register():
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
    del bpy.types.Scene.vircadia_hide_collisions
    del bpy.types.Scene.vircadia_collisions_wireframe
    del bpy.types.Scene.vircadia_hide_lod_levels
    del bpy.types.Scene.vircadia_hide_armatures

if __name__ == "__main__":
    register()