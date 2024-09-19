import bpy
from bpy.types import Operator
from ..lightmap import generateLightmaps, lightmap_utils

class VIRCADIA_OT_generate_lightmaps(Operator):
    bl_idname = "vircadia.generate_lightmaps"
    bl_label = "Generate Lightmaps"
    bl_description = "Generate lightmaps for the selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        
        # Set the "Hide Lightmaps" toggle to True
        scene.vircadia_hide_lightmaps = True

        # Check for vircadia_lightmapData object
        self.check_and_create_lightmap_data_object(context)

        # Update lightmap configuration
        lightmap_settings = lightmap_utils.get_lightmap_settings(scene)
        bake_settings = lightmap_utils.get_bake_settings(scene)

        # Get visible selected objects
        visible_selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH' and not obj.hide_get()]

        if not visible_selected_objects:
            self.report({'WARNING'}, "No visible mesh objects selected. Please select at least one visible mesh object.")
            return {'CANCELLED'}

        # Generate lightmaps
        generateLightmaps.generate_lightmaps(visible_selected_objects, lightmap_settings, bake_settings)

        self.report({'INFO'}, "Lightmap generation completed")
        return {'FINISHED'}

    def check_and_create_lightmap_data_object(self, context):
        # Store the current selection and active object
        original_selection = context.selected_objects
        original_active = context.active_object

        lightmap_data_obj = bpy.data.objects.get("vircadia_lightmapData")

        if not lightmap_data_obj:
            # Create or get the vircadia_lightmapData collection
            lightmap_data_collection = bpy.data.collections.get("vircadia_lightmapData")
            if not lightmap_data_collection:
                lightmap_data_collection = bpy.data.collections.new("vircadia_lightmapData")
                context.scene.collection.children.link(lightmap_data_collection)

            # Create the vircadia_lightmapData plane
            bpy.ops.mesh.primitive_plane_add(size=1, enter_editmode=False, location=(0, 0, 0))
            lightmap_data_obj = context.active_object
            lightmap_data_obj.name = "vircadia_lightmapData"

            # Move the object to the vircadia_lightmapData collection
            for col in lightmap_data_obj.users_collection:
                col.objects.unlink(lightmap_data_obj)
            lightmap_data_collection.objects.link(lightmap_data_obj)

            self.report({'INFO'}, "Created vircadia_lightmapData object")

        # Restore the original selection and active object
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selection:
            obj.select_set(True)
        if original_active:
            context.view_layer.objects.active = original_active

    @classmethod
    def poll(cls, context):
        return any(obj.type == 'MESH' and not obj.hide_get() for obj in context.selected_objects)

class VIRCADIA_OT_clear_lightmaps(Operator):
    bl_idname = "vircadia.clear_lightmaps"
    bl_label = "Clear Lightmaps"
    bl_description = "Clear all lightmaps from selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects
        for obj in selected_objects:
            if obj.type == 'MESH':
                self.clear_lightmap(obj)
        
        self.report({'INFO'}, f"Cleared lightmaps from {len(selected_objects)} objects")
        return {'FINISHED'}

    def clear_lightmap(self, obj):
        if obj.data.uv_layers.get("Lightmap"):
            obj.data.uv_layers.remove(obj.data.uv_layers["Lightmap"])
        
        for material_slot in obj.material_slots:
            if material_slot.material:
                self.remove_lightmap_node(material_slot.material)

    def remove_lightmap_node(self, material):
        if material.use_nodes:
            nodes = material.node_tree.nodes
            lightmap_node = next((node for node in nodes if node.type == 'TEX_IMAGE' and node.name.startswith("Lightmap")), None)
            if lightmap_node:
                nodes.remove(lightmap_node)

    @classmethod
    def poll(cls, context):
        return context.selected_objects

class VIRCADIA_OT_pack_lightmap_uvs(Operator):
    bl_idname = "vircadia.pack_lightmap_uvs"
    bl_label = "Pack Lightmap UVs"
    bl_description = "Pack lightmap UVs for selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
        
        if not selected_objects:
            self.report({'WARNING'}, "No mesh objects selected")
            return {'CANCELLED'}
        
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected_objects:
            obj.select_set(True)
        
        context.view_layer.objects.active = selected_objects[0]
        
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        
        # Ensure 'Lightmap' UV layer exists and is active
        for obj in selected_objects:
            if "Lightmap" not in obj.data.uv_layers:
                obj.data.uv_layers.new(name="Lightmap")
            obj.data.uv_layers["Lightmap"].active = True
        
        bpy.ops.uv.lightmap_pack(
            PREF_CONTEXT='ALL_FACES',
            PREF_PACK_IN_ONE=True,
            PREF_NEW_UVLAYER=False,
            PREF_APPLY_IMAGE=False,
            PREF_IMG_PX_SIZE=1024,
            PREF_BOX_DIV=12,
            PREF_MARGIN_DIV=0.1
        )
        
        bpy.ops.object.mode_set(mode='OBJECT')
        
        self.report({'INFO'}, f"Packed lightmap UVs for {len(selected_objects)} objects")
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return context.selected_objects

def register():
    bpy.utils.register_class(VIRCADIA_OT_generate_lightmaps)
    bpy.utils.register_class(VIRCADIA_OT_clear_lightmaps)
    bpy.utils.register_class(VIRCADIA_OT_pack_lightmap_uvs)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_OT_pack_lightmap_uvs)
    bpy.utils.unregister_class(VIRCADIA_OT_clear_lightmaps)
    bpy.utils.unregister_class(VIRCADIA_OT_generate_lightmaps)

if __name__ == "__main__":
    register()