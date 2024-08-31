import bpy
from bpy.types import Panel, Scene
from bpy.props import BoolProperty
from ..utils import property_utils

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

class VIRCADIA_PT_custom_properties(Panel):
    bl_label = "Vircadia Properties"
    bl_idname = "VIEW3D_PT_vircadia_custom_properties"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vircadia"

    @classmethod
    def poll(cls, context):
        return context.object is not None and (context.object.get("name") is not None or context.object.get("type") == "Zone")

    def draw(self, context):
        layout = self.layout
        obj = context.object

        # Get the custom property "name" for the panel title
        if obj.get("type") == "Zone":
            custom_name = obj.name
        else:
            custom_name = obj.get("name", "Unnamed")

        layout.label(text=f"{custom_name}")

        self.draw_custom_properties(context, layout, obj)

    def draw_custom_properties(self, context, layout, obj):
        # Get custom properties, sort alphabetically, and filter out specific properties
        single_word_properties = {}
        grouped_properties = {}
        processed_keys = set()

        for key in sorted(obj.keys()):
            if property_utils.should_filter_property(key) or key in processed_keys:
                continue

            parts = key.split('_')
            if len(parts) == 1 or (len(parts) == 2 and len(parts[1]) == 1):
                if self.is_color_component(key):
                    base_name = parts[0]
                    if all(f"{base_name}_{color}" in obj for color in ['red', 'green', 'blue']):
                        single_word_properties[base_name] = {color: f"{base_name}_{color}" for color in ['red', 'green', 'blue']}
                        processed_keys.update(single_word_properties[base_name].values())
                elif self.is_vector_component(key):
                    base_name = parts[0]
                    vector_components = ['x', 'y', 'z']
                    if f"{base_name}_w" in obj:
                        vector_components.append('w')
                    if all(f"{base_name}_{axis}" in obj for axis in vector_components):
                        single_word_properties[base_name] = {axis: f"{base_name}_{axis}" for axis in vector_components}
                        processed_keys.update(single_word_properties[base_name].values())
                else:
                    single_word_properties[key] = key
            else:
                group_name = parts[0]
                sub_name = "_".join(parts[1:])
                if self.is_color_component(key):
                    base_name = "_".join(parts[:-1])
                    if all(f"{base_name}_{color}" in obj for color in ['red', 'green', 'blue']):
                        if group_name not in grouped_properties:
                            grouped_properties[group_name] = {}
                        grouped_properties[group_name][base_name] = {color: f"{base_name}_{color}" for color in ['red', 'green', 'blue']}
                        processed_keys.update(grouped_properties[group_name][base_name].values())
                elif self.is_vector_component(key):
                    base_name = "_".join(parts[:-1])
                    vector_components = ['x', 'y', 'z']
                    if f"{base_name}_w" in obj:
                        vector_components.append('w')
                    if all(f"{base_name}_{axis}" in obj for axis in vector_components):
                        if group_name not in grouped_properties:
                            grouped_properties[group_name] = {}
                        grouped_properties[group_name][base_name] = {axis: f"{base_name}_{axis}" for axis in vector_components}
                        processed_keys.update(grouped_properties[group_name][base_name].values())
                else:
                    if group_name not in grouped_properties:
                        grouped_properties[group_name] = {}
                    grouped_properties[group_name][sub_name] = key

        # Draw single-word properties at the top
        for key, value in single_word_properties.items():
            if isinstance(value, dict):
                if self.is_color_property(value):
                    self.draw_color_property(layout, obj, key, value)
                elif self.is_vector_property(value):
                    self.draw_vector_property(layout, obj, key, value)
            else:
                self.draw_property(layout, obj, key, value)

        # Draw grouped properties
        for group_name, group_props in grouped_properties.items():
            box = layout.box()
            box.label(text=group_name.capitalize())

            if group_name == "keyLight":
                self.draw_keylight_properties(box, obj, group_props)
            else:
                for key, value in group_props.items():
                    if isinstance(value, dict):
                        if self.is_color_property(value):
                            self.draw_color_property(box, obj, key, value)
                        elif self.is_vector_property(value):
                            self.draw_vector_property(box, obj, key, value)
                    else:
                        self.draw_property(box, obj, key, value)

    def draw_keylight_properties(self, layout, obj, properties):
        # Draw keyLight color
        color_props = {
            "red": properties.get("color", {}).get("red", "keyLight_color_red"),
            "green": properties.get("color", {}).get("green", "keyLight_color_green"),
            "blue": properties.get("color", {}).get("blue", "keyLight_color_blue")
        }
        self.draw_color_property(layout, obj, "Color", color_props)

        # Draw keyLight direction
        direction_props = {
            "x": properties.get("direction", {}).get("x", "keyLight_direction_x"),
            "y": properties.get("direction", {}).get("y", "keyLight_direction_y"),
            "z": properties.get("direction", {}).get("z", "keyLight_direction_z")
        }
        self.draw_vector_property(layout, obj, "Direction", direction_props)

        # Draw keyLight intensity
        intensity_prop = properties.get("intensity", "keyLight_intensity")
        self.draw_property(layout, obj, "Intensity", intensity_prop)

    def is_color_component(self, key):
        return key.endswith(("red", "green", "blue"))

    def is_vector_component(self, key):
        return key.endswith(("x", "y", "z", "w"))

    def is_color_property(self, value):
        return all(color in value for color in ["red", "green", "blue"])

    def is_vector_property(self, value):
        return all(axis in value for axis in ["x", "y", "z"])

    def draw_property(self, layout, obj, prop_name, full_prop_name):
        row = layout.row()
        row.label(text=prop_name.capitalize())
        row.prop(obj, f'["{full_prop_name}"]', text="")

    def draw_color_property(self, layout, obj, base_name, color_components):
        row = layout.row(align=True)
        row.label(text=base_name.capitalize())
        for color, label in zip(['red', 'green', 'blue'], ['R', 'G', 'B']):
            col = row.column(align=True)
            col.prop(obj, f'["{color_components[color]}"]', text=label)

    def draw_vector_property(self, layout, obj, base_name, vector_components):
        row = layout.row(align=True)
        row.label(text=base_name.capitalize())
        axes = ['w', 'x', 'y', 'z'] if 'w' in vector_components else ['x', 'y', 'z']
        for axis in axes:
            col = row.column(align=True)
            col.prop(obj, f'["{vector_components[axis]}"]', text=axis.upper())

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
    bpy.utils.register_class(VIRCADIA_PT_custom_properties)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_PT_custom_properties)
    bpy.utils.unregister_class(VIRCADIA_PT_main_panel)
    del bpy.types.Scene.vircadia_hide_collisions
    del bpy.types.Scene.vircadia_collisions_wireframe
    del bpy.types.Scene.vircadia_hide_lod_levels
    del bpy.types.Scene.vircadia_hide_armatures

if __name__ == "__main__":
    register()