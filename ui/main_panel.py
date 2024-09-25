import bpy
from bpy.types import Panel, Operator
from bpy.props import BoolProperty, StringProperty

def update_visibility(self, context):
    for obj in bpy.data.objects:
        update_object_visibility(obj, context.scene)
    update_lightmap_visibility(context.scene)

    # Update scene world based on hide_lightmaps state
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    if context.scene.vircadia_hide_lightmaps:
                        # Restore previous scene world state
                        space.shading.use_scene_world = context.scene.vircadia_previous_scene_world
                    else:
                        # Store current state and set scene world to False when showing lightmaps
                        context.scene.vircadia_previous_scene_world = space.shading.use_scene_world
                        space.shading.use_scene_world = False

def update_object_visibility(obj, scene):
    # Check if object is a collision object
    is_collision = any(name in obj.name.lower() for name in ["collision", "collider", "collides"]) or \
                   (obj.parent and any(name in obj.parent.name.lower() for name in ["collision", "collider", "collides"]))

    # Check if object is an LOD level (except LOD0)
    is_lod = any(f"_LOD{i}" in obj.name for i in range(1, 100))  # Checking up to LOD99

    # Update visibility based on settings
    if is_collision:
        obj.hide_set(scene.vircadia_hide_collisions)
        obj.display_type = 'WIRE' if scene.vircadia_collisions_wireframe else 'TEXTURED'
    elif is_lod:
        obj.hide_set(scene.vircadia_hide_lod_levels)
    elif obj.type == 'ARMATURE':
        obj.hide_set(scene.vircadia_hide_armatures)

    # Apply settings to children recursively
    for child in obj.children:
        update_object_visibility(child, scene)

def update_lightmap_visibility(scene):
    if scene.vircadia_hide_lightmaps:
        hide_lightmaps(scene)
    else:
        show_lightmaps(scene)

def hide_lightmaps(scene):
    print("Starting to hide lightmaps...")
    for mat in bpy.data.materials:
        if mat.use_nodes:
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Find lightmap-related nodes
            lightmap_node = next((node for node in nodes if node.type == 'TEX_IMAGE' and 'vircadia_lightmapData' in node.label), None)
            mix_node = next((node for node in nodes if node.type == 'MIX_RGB' and lightmap_node in [link.from_node for link in node.inputs[2].links]), None)
            principled_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)

            if lightmap_node and mix_node and principled_node:
                # Disconnect and mute lightmap node
                for link in lightmap_node.outputs[0].links:
                    links.remove(link)
                lightmap_node.mute = True

                # Disconnect and mute mix node
                for link in mix_node.outputs[0].links:
                    links.remove(link)
                mix_node.mute = True

                # Reconnect the original base color
                if mix_node.inputs[1].is_linked:
                    original_color_socket = mix_node.inputs[1].links[0].from_socket
                    links.new(original_color_socket, principled_node.inputs['Base Color'])

            # Disable and disconnect UV Map nodes for lightmaps
            uv_map_nodes = [node for node in nodes if node.type == 'UVMAP' and node.uv_map == "Lightmap"]
            for uv_node in uv_map_nodes:
                for link in uv_node.outputs[0].links:
                    links.remove(link)
                uv_node.mute = True

    # Handle lights
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            if "lightmap" not in obj.name.lower():
                obj.hide_viewport = False
                obj.hide_render = False

    print("Lightmaps hidden and connections restored.")

def show_lightmaps(scene):
    print("Starting to show lightmaps...")
    lightmaps_found = False
    for mat in bpy.data.materials:
        if mat.use_nodes:
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Find and enable lightmap-related nodes
            lightmap_node = next((node for node in nodes if node.type == 'TEX_IMAGE' and node.label.startswith('vircadia_lightmapData_')), None)
            if lightmap_node:
                lightmap_node.mute = False
                lightmaps_found = True

                # Get the mesh object using this material
                obj = next((obj for obj in bpy.data.objects if obj.type == 'MESH' and mat.name in obj.material_slots), None)
                if obj:
                    mesh = obj.data
                    
                    # Ensure UV Map node for the first UV map exists and is connected
                    first_uv_map = mesh.uv_layers[0] if mesh.uv_layers else None
                    if first_uv_map:
                        uv_map_node = next((node for node in nodes if node.type == 'UVMAP' and node.uv_map == first_uv_map.name), None)
                        if not uv_map_node:
                            uv_map_node = nodes.new(type='ShaderNodeUVMap')
                            uv_map_node.uv_map = first_uv_map.name
                            uv_map_node.location = (lightmap_node.location[0] - 300, lightmap_node.location[1] + 200)
                        uv_map_node.mute = False
                        
                        # Connect to other texture nodes
                        for node in nodes:
                            if node.type == 'TEX_IMAGE' and node != lightmap_node:
                                if not node.inputs[0].is_linked:
                                    links.new(uv_map_node.outputs[0], node.inputs[0])

                    # Ensure UV Map node for Lightmap exists and is connected
                    lightmap_uv = next((uv for uv in mesh.uv_layers if uv.name == "Lightmap"), None)
                    if lightmap_uv:
                        lightmap_uv_node = next((node for node in nodes if node.type == 'UVMAP' and node.uv_map == "Lightmap"), None)
                        if not lightmap_uv_node:
                            lightmap_uv_node = nodes.new(type='ShaderNodeUVMap')
                            lightmap_uv_node.uv_map = "Lightmap"
                            lightmap_uv_node.location = (lightmap_node.location[0] - 300, lightmap_node.location[1])
                        lightmap_uv_node.mute = False
                        if not lightmap_node.inputs[0].is_linked:
                            links.new(lightmap_uv_node.outputs[0], lightmap_node.inputs[0])

                # Ensure Mix node exists and is connected
                mix_node = next((node for node in nodes if node.type == 'MIX_RGB' and lightmap_node in [link.from_node for link in node.inputs[2].links]), None)
                if not mix_node:
                    mix_node = nodes.new(type='ShaderNodeMixRGB')
                    mix_node.blend_type = 'MULTIPLY'
                    mix_node.inputs[0].default_value = 1.0
                    mix_node.location = (lightmap_node.location[0] + 300, lightmap_node.location[1])
                mix_node.mute = False

                # Connect lightmap to Mix node if not already connected
                if not mix_node.inputs[2].is_linked:
                    links.new(lightmap_node.outputs[0], mix_node.inputs[2])

                # Find Principled BSDF node and connect Mix node
                principled_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)
                if principled_node:
                    # Copy the base color from Principled BSDF to Mix node
                    if principled_node.inputs['Base Color'].is_linked:
                        original_color_socket = principled_node.inputs['Base Color'].links[0].from_socket
                        links.new(original_color_socket, mix_node.inputs[1])
                    else:
                        # If not linked, copy the color value
                        mix_node.inputs[1].default_value = principled_node.inputs['Base Color'].default_value

                    # Remove existing links to Base Color
                    for link in principled_node.inputs['Base Color'].links:
                        links.remove(link)
                    
                    # Connect Mix node to Principled BSDF Base Color
                    links.new(mix_node.outputs[0], principled_node.inputs['Base Color'])

    # Handle lights
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            if "lightmap" not in obj.name.lower():
                obj.hide_viewport = True
                obj.hide_render = True

    if not lightmaps_found:
        scene.vircadia_hide_lightmaps = True
        bpy.ops.vircadia.show_warning('INVOKE_DEFAULT', message="No lightmaps found in the scene.")
    
    print("Lightmaps shown and materials modified.")

class VIRCADIA_OT_show_warning(Operator):
    bl_idname = "vircadia.show_warning"
    bl_label = "Vircadia Warning"
    bl_options = {'INTERNAL'}

    message: StringProperty()

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.label(text=self.message)

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
    bl_order = 0

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

        # New "Selected to Collision" button
        box.operator("vircadia.selected_to_collision", text="Selected to Collision")

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
        box.prop(scene, "vircadia_hide_lightmaps", text="Hide Lightmaps")

def register():
    bpy.utils.register_class(VIRCADIA_OT_paste_content_path)
    bpy.utils.register_class(VIRCADIA_OT_convert_collisions)
    bpy.utils.register_class(VIRCADIA_OT_process_lod)
    bpy.utils.register_class(VIRCADIA_OT_show_warning)
    bpy.types.Scene.vircadia_content_path = StringProperty(
        name="Content Path",
        description="Path to the content directory for Vircadia assets",
        default="",
    )
    bpy.types.Scene.vircadia_hide_collisions = BoolProperty(
        name="Hide Collisions",
        description="Hide collision objects",
        default=True,
        update=update_hide_collisions
    )
    bpy.types.Scene.vircadia_collisions_wireframe = BoolProperty(
        name="Collisions as Wireframe",
        description="Display collision objects as wireframe",
        default=False,
        update=update_collisions_wireframe
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
    bpy.types.Scene.vircadia_hide_lightmaps = BoolProperty(
        name="Hide Lightmaps",
        description="Hide lightmaps",
        default=True,
        update=update_visibility
    )
    bpy.types.Scene.vircadia_previous_scene_world = BoolProperty(
        name="Previous Scene World State",
        description="Stores the previous state of use_scene_world",
        default=True
    )
    bpy.utils.register_class(VIRCADIA_PT_main_panel)
    
def update_hide_collisions(self, context):
    if self.vircadia_hide_collisions:
        self.vircadia_collisions_wireframe = False
    update_visibility(self, context)

def update_collisions_wireframe(self, context):
    if self.vircadia_collisions_wireframe:
        self.vircadia_hide_collisions = False
    update_visibility(self, context)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_PT_main_panel)
    bpy.utils.unregister_class(VIRCADIA_OT_show_warning)
    bpy.utils.unregister_class(VIRCADIA_OT_process_lod)
    bpy.utils.unregister_class(VIRCADIA_OT_convert_collisions)
    bpy.utils.unregister_class(VIRCADIA_OT_paste_content_path)
    del bpy.types.Scene.vircadia_hide_collisions
    del bpy.types.Scene.vircadia_collisions_wireframe
    del bpy.types.Scene.vircadia_hide_lod_levels
    del bpy.types.Scene.vircadia_hide_armatures
    del bpy.types.Scene.vircadia_hide_lightmaps
    del bpy.types.Scene.vircadia_content_path
    del bpy.types.Scene.vircadia_previous_scene_world

if __name__ == "__main__":
    register()