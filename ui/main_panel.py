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
    # Restore original material states and light visibility
    for mat in bpy.data.materials:
        if "original_nodes" in mat:
            mat.node_tree.nodes.clear()
            for node_data in mat["original_nodes"]:
                node = mat.node_tree.nodes.new(type=node_data["type"])
                node.name = node_data["name"]
                node.label = node_data["label"]
                node.location = node_data["location"]
                
                # Special handling for image texture nodes
                if node.type == 'TEX_IMAGE' and "image" in node_data:
                    if node_data["image"] is not None:
                        node.image = bpy.data.images.get(node_data["image"])
                
                for input_name, input_data in node_data["inputs"].items():
                    if input_name not in node.inputs:
                        continue  # Skip inputs that no longer exist
                    if input_data["is_linked"]:
                        continue  # We'll reconnect links later
                    if hasattr(node.inputs[input_name], "default_value") and input_data["default_value"] is not None:
                        try:
                            node.inputs[input_name].default_value = input_data["default_value"]
                        except (TypeError, AttributeError):
                            print(f"Warning: Could not set default value for input '{input_name}' on node '{node.name}'")
            
            # Restore links
            for link_data in mat["original_links"]:
                try:
                    from_node = mat.node_tree.nodes[link_data["from_node"]]
                    to_node = mat.node_tree.nodes[link_data["to_node"]]
                    from_socket = from_node.outputs[link_data["from_socket"]]
                    to_socket = to_node.inputs[link_data["to_socket"]]
                    mat.node_tree.links.new(from_socket, to_socket)
                except KeyError:
                    print(f"Warning: Could not restore link {link_data}")
            
            del mat["original_nodes"]
            del mat["original_links"]
    
    # Restore light visibility
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT' and "original_hide" in obj:
            obj.hide_set(obj["original_hide"])
            del obj["original_hide"]

    print("Lightmaps hidden and original states restored.")

def show_lightmaps(scene):
    print("Starting to show lightmaps...")
    lightmaps_found = False
    for mat in bpy.data.materials:
        if mat.use_nodes:
            # Store original material state
            mat["original_nodes"] = [{
                "type": node.bl_idname,
                "name": node.name,
                "label": node.label,
                "location": node.location[:],
                "inputs": {input.name: {"default_value": input.default_value if hasattr(input, "default_value") else None, 
                                        "is_linked": input.is_linked} for input in node.inputs},
                "image": node.image.name if node.type == 'TEX_IMAGE' and node.image else None
            } for node in mat.node_tree.nodes]
            mat["original_links"] = [{
                "from_node": link.from_node.name,
                "to_node": link.to_node.name,
                "from_socket": link.from_socket.name,
                "to_socket": link.to_socket.name
            } for link in mat.node_tree.links]

            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Find Lightmap texture node
            lightmap_node = next((node for node in nodes if node.type == 'TEX_IMAGE' and 'vircadia_lightmapData' in node.label), None)
            if lightmap_node:
                lightmaps_found = True
                # Add UV Map node for Lightmap
                uv_map_node = nodes.new(type='ShaderNodeUVMap')
                uv_map_node.uv_map = "Lightmap"  # Assume second UV map is named Lightmap
                links.new(uv_map_node.outputs[0], lightmap_node.inputs[0])

                # Add Mix node
                mix_node = nodes.new(type='ShaderNodeMixRGB')
                mix_node.blend_type = 'MULTIPLY'
                mix_node.inputs[0].default_value = 1.0  # Set factor to 1.0

                # Find Principled BSDF node
                principled_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)
                if principled_node:
                    # Store original base color
                    original_color = principled_node.inputs['Base Color'].default_value[:]

                    # Set up connections
                    if principled_node.inputs['Base Color'].is_linked:
                        original_color_input = principled_node.inputs['Base Color'].links[0].from_socket
                        links.new(original_color_input, mix_node.inputs[1])
                    else:
                        mix_node.inputs[1].default_value = original_color

                    links.new(lightmap_node.outputs[0], mix_node.inputs[2])
                    links.new(mix_node.outputs[0], principled_node.inputs['Base Color'])

            # Add UV Map nodes for other texture nodes
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node != lightmap_node:
                    uv_map_node = nodes.new(type='ShaderNodeUVMap')
                    uv_map_node.uv_map = "UVMap"  # Assume first UV map is named UVMap
                    links.new(uv_map_node.outputs[0], node.inputs[0])

    # Handle lights
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            obj["original_hide"] = obj.hide_get()
            if "lightmap" not in obj.name.lower():
                obj.hide_set(True)

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