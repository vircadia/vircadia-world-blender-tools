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
        if not context.selected_objects:
            return False
        
        collision_keywords = ["collision", "collides", "collider", "collisions", "colliders"]
        
        for obj in context.selected_objects:
            # Check if vircadia_lightmapData is selected
            if obj.name == "vircadia_lightmapData":
                return False
            
            # Check if any collision object is selected
            if any(keyword in obj.name.lower() for keyword in collision_keywords):
                return False
            
            if obj.type == 'MESH' and not obj.hide_get():
                # Check if the object doesn't have lightmaps
                if not obj.data.uv_layers.get("Lightmap"):
                    # Check if the object's materials don't have lightmap nodes
                    for material_slot in obj.material_slots:
                        if material_slot.material and material_slot.material.use_nodes:
                            has_lightmap_node = any(
                                node.type == 'TEX_IMAGE' and node.label.startswith('vircadia_lightmapData_')
                                for node in material_slot.material.node_tree.nodes
                            )
                            if not has_lightmap_node:
                                return True
        
        return False

class VIRCADIA_OT_clear_lightmaps(Operator):
    bl_idname = "vircadia.clear_lightmaps"
    bl_label = "Clear Lightmaps"
    bl_description = "Clear lightmaps from selected objects and all objects using the same lightmaps"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Set hide_lightmaps to True
        context.scene.vircadia_hide_lightmaps = True

        selected_objects = context.selected_objects
        removed_materials = set()
        affected_lightmap_ids = set()

        # First pass: identify lightmap IDs from selected objects
        for obj in selected_objects:
            if obj.type == 'MESH':
                self.identify_lightmap_ids(obj, affected_lightmap_ids)

        # Second pass: clear lightmaps from objects using the identified lightmap IDs
        affected_objects = self.find_affected_objects(affected_lightmap_ids)
        for obj in affected_objects:
            self.clear_lightmap(obj, removed_materials, affected_lightmap_ids)

        # Remove materials from vircadia_lightmapData object
        self.remove_materials_from_lightmap_data(removed_materials)

        self.report({'INFO'}, f"Cleared lightmaps from {len(affected_objects)} objects and removed {len(removed_materials)} materials from vircadia_lightmapData")
        return {'FINISHED'}

    def identify_lightmap_ids(self, obj, affected_lightmap_ids):
        for material_slot in obj.material_slots:
            if material_slot.material and material_slot.material.use_nodes:
                for node in material_slot.material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.label.startswith('vircadia_lightmapData_'):
                        lightmap_id = node.label.split('_')[2]
                        affected_lightmap_ids.add(lightmap_id)

    def find_affected_objects(self, affected_lightmap_ids):
        affected_objects = set()
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                for material_slot in obj.material_slots:
                    if material_slot.material and material_slot.material.use_nodes:
                        for node in material_slot.material.node_tree.nodes:
                            if node.type == 'TEX_IMAGE' and node.label.startswith('vircadia_lightmapData_'):
                                lightmap_id = node.label.split('_')[2]
                                if lightmap_id in affected_lightmap_ids:
                                    affected_objects.add(obj)
                                    break
                    if obj in affected_objects:
                        break
        return affected_objects

    def clear_lightmap(self, obj, removed_materials, affected_lightmap_ids):
        # Remove Lightmap UV layer if it exists
        if obj.data.uv_layers.get("Lightmap"):
            obj.data.uv_layers.remove(obj.data.uv_layers["Lightmap"])
        
        # Clear lightmap nodes from materials
        for material_slot in obj.material_slots:
            if material_slot.material:
                self.remove_lightmap_node(material_slot.material, removed_materials, affected_lightmap_ids)

    def remove_lightmap_node(self, material, removed_materials, affected_lightmap_ids):
        if material.use_nodes:
            nodes = material.node_tree.nodes
            links = material.node_tree.links

            # Find and remove all lightmap-related nodes
            nodes_to_remove = []
            for node in nodes:
                if node.type == 'TEX_IMAGE' and node.label.startswith('vircadia_lightmapData_'):
                    lightmap_id = node.label.split('_')[2]
                    if lightmap_id in affected_lightmap_ids:
                        nodes_to_remove.append(node)
                        removed_materials.add(lightmap_id)
                elif node.type == 'MIX_RGB' and any(input.is_linked and input.links[0].from_node in nodes_to_remove for input in node.inputs):
                    nodes_to_remove.append(node)
                elif node.type == 'UVMAP' and node.uv_map == "Lightmap":
                    nodes_to_remove.append(node)

            # Find the Principled BSDF node
            principled_node = next((node for node in nodes if node.type == 'BSDF_PRINCIPLED'), None)

            # Reconnect original base color and remove nodes
            for node in nodes_to_remove:
                if node.type == 'MIX_RGB' and node.inputs[1].is_linked:
                    original_color_socket = node.inputs[1].links[0].from_socket
                    if principled_node:
                        for link in principled_node.inputs['Base Color'].links:
                            links.remove(link)
                        links.new(original_color_socket, principled_node.inputs['Base Color'])
                nodes.remove(node)

            # Cleanup: remove any disconnected UV Map nodes
            for node in nodes:
                if node.type == 'UVMAP' and not node.outputs[0].links:
                    nodes.remove(node)

        print(f"Removed lightmap-related nodes from material: {material.name}")

    def remove_materials_from_lightmap_data(self, removed_materials):
        lightmap_data_obj = bpy.data.objects.get("vircadia_lightmapData")
        if lightmap_data_obj:
            materials_to_remove = []
            for mat in lightmap_data_obj.data.materials:
                if mat and mat.name.startswith("vircadia_lightmapData_"):
                    mat_id = mat.name.split('_')[2]
                    if mat_id in removed_materials:
                        materials_to_remove.append(mat)

            # Remove materials and clear slots
            for mat in materials_to_remove:
                for i, slot in enumerate(lightmap_data_obj.material_slots):
                    if slot.material == mat:
                        lightmap_data_obj.data.materials[i] = None
                bpy.data.materials.remove(mat)

            # Set the lightmap_data_obj as active
            bpy.context.view_layer.objects.active = lightmap_data_obj

            # Remove empty material slots
            for i in range(len(lightmap_data_obj.material_slots) - 1, -1, -1):
                lightmap_data_obj.active_material_index = i
                if lightmap_data_obj.material_slots[i].material is None:
                    bpy.ops.object.material_slot_remove()

            print(f"Removed {len(materials_to_remove)} materials and cleared empty slots from vircadia_lightmapData")
            print(f"Remaining material slots: {len(lightmap_data_obj.material_slots)}")
        else:
            print("vircadia_lightmapData object not found")

    @classmethod
    def poll(cls, context):
        if not context.selected_objects:
            return False
        
        for obj in context.selected_objects:
            if obj.type == 'MESH':
                # Check for Lightmap UV layer
                if obj.data.uv_layers.get("Lightmap"):
                    return True
                
                # Check for lightmap nodes in materials
                for material_slot in obj.material_slots:
                    if material_slot.material and material_slot.material.use_nodes:
                        for node in material_slot.material.node_tree.nodes:
                            if node.type == 'TEX_IMAGE' and node.label.startswith('vircadia_lightmapData_'):
                                return True
        
        return False

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