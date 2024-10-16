import bpy
from typing import Dict, Any, List, Optional
import json

from vircadia_world_sdk_py.shared.modules.vircadia_world_meta.python.world import (
    TableWorldGLTF, TableScene, TableNode, TableMesh, TableMaterial, TableTexture,
    TableImage, TableSampler, TableAnimation, TableSkin, TableCamera, TableBuffer,
    TableBufferView, TableAccessor, TableMetadata
)

class WorldGLTFToBlenderImport:
    def __init__(self):
        self.uuid_to_object: Dict[str, bpy.types.ID] = {}

    def import_world_gltf(self, world_gltf_data: TableWorldGLTF) -> None:
        # Import the main world data
        # This might set up global properties or metadata
        if world_gltf_data.vircadia_name:
            bpy.context.scene.name = world_gltf_data.vircadia_name
        # Import metadata
        if world_gltf_data.vircadia_metadata:
            self.import_metadata(world_gltf_data.vircadia_metadata, bpy.context.scene)

    def import_scene(self, scene_data: TableScene) -> bpy.types.Scene:
        scene_name = scene_data.gltf_name if scene_data.gltf_name is not None else "Imported Scene"
        scene = bpy.data.scenes.new(name=scene_name)
        self.uuid_to_object[scene_data.vircadia_uuid] = scene
        
        if scene_data.vircadia_babylonjs_scene_clearColor:
            if scene.world and scene.world.node_tree:
                background_node = scene.world.node_tree.nodes.get("Background")
                if background_node and background_node.inputs.get("Color"):
                    background_node.inputs["Color"].default_value = scene_data.vircadia_babylonjs_scene_clearColor
        
        # Import other scene properties
        if scene_data.vircadia_babylonjs_scene_gravity:
            scene.gravity = scene_data.vircadia_babylonjs_scene_gravity
        if scene_data.vircadia_babylonjs_scene_physicsEnabled is not None:
            scene.use_gravity = scene_data.vircadia_babylonjs_scene_physicsEnabled
        
        return scene

    def import_metadata(self, metadata: TableMetadata, target_object: bpy.types.ID) -> None:
        if isinstance(target_object, bpy.types.ID):
            if metadata.key is not None:
                target_object[f"vircadia_metadata_{metadata.key}"] = metadata.values_text or metadata.values_numeric or metadata.values_boolean or metadata.values_timestamp

    def import_babylon_properties(self, data: TableNode, target_object: bpy.types.Object) -> None:
        if isinstance(target_object, bpy.types.Object):
            if data.vircadia_babylonjs_lod_mode:
                target_object['babylonjs_lod_mode'] = data.vircadia_babylonjs_lod_mode
            if data.vircadia_babylonjs_lod_distance:
                target_object['babylonjs_lod_distance'] = data.vircadia_babylonjs_lod_distance
            # ... handle other Babylon.js properties ...

    def import_scripts(self, data: TableNode, target_object: bpy.types.Object) -> None:
        if isinstance(target_object, bpy.types.Object):
            if data.vircadia_babylonjs_script_agent_script_raw_file_url:
                target_object['agent_scripts'] = data.vircadia_babylonjs_script_agent_script_raw_file_url
            if data.vircadia_babylonjs_script_persistent_script_raw_file_url:
                target_object['persistent_scripts'] = data.vircadia_babylonjs_script_persistent_script_raw_file_url

    def import_node(self, node_data: TableNode) -> bpy.types.Object:
        obj = bpy.data.objects.new(node_data.gltf_name or 'Imported Node', None)
        self.uuid_to_object[node_data.vircadia_uuid] = obj
        
        obj.location = node_data.gltf_translation or (0, 0, 0)
        obj.rotation_quaternion = node_data.gltf_rotation or (1, 0, 0, 0)
        obj.scale = node_data.gltf_scale or (1, 1, 1)

        if node_data.vircadia_babylonjs_billboard_mode:
            # Set up billboard constraints or properties
            pass

        self.import_babylon_properties(node_data, obj)
        self.import_scripts(node_data, obj)

        if bpy.context:
            bpy.context.scene.collection.objects.link(obj)
        return obj

    def import_mesh(self, mesh_data: TableMesh) -> bpy.types.Object:
        mesh = bpy.data.meshes.new(name=mesh_data.gltf_name or 'Imported Mesh')
        obj = bpy.data.objects.new(mesh_data.gltf_name or 'Imported Mesh', mesh)
        self.uuid_to_object[mesh_data.vircadia_uuid] = obj

        # Create mesh geometry
        # This is a placeholder. You'll need to handle primitives properly.
        vertices = []
        faces = []
        for primitive in mesh_data.gltf_primitives or []:
            # Extract vertex and index data from primitive
            pass
        
        mesh.from_pydata(vertices, [], faces)
        mesh.update()

        self.import_babylon_properties(mesh_data, obj)
        self.import_scripts(mesh_data, obj)

        if bpy.context:
            bpy.context.scene.collection.objects.link(obj)
        return obj

    def import_material(self, material_data: TableMaterial) -> bpy.types.Material:
        mat = bpy.data.materials.new(name=material_data.gltf_name or 'Imported Material')
        self.uuid_to_object[material_data.vircadia_uuid] = mat

        mat.use_nodes = True
        if mat.node_tree:
            nodes = mat.node_tree.nodes
        
        if material_data.gltf_pbrMetallicRoughness:
            pbr = material_data.gltf_pbrMetallicRoughness
            principled = nodes.get("Principled BSDF")
            if principled:
                if 'baseColorFactor' in pbr:
                    principled.inputs["Base Color"].default_value = pbr['baseColorFactor']
                if 'metallicFactor' in pbr:
                    principled.inputs["Metallic"].default_value = pbr['metallicFactor']
                if 'roughnessFactor' in pbr:
                    principled.inputs["Roughness"].default_value = pbr['roughnessFactor']

        # Handle other material properties (normal map, occlusion, etc.)
        
        return mat

    def import_texture(self, texture_data: TableTexture) -> bpy.types.Image:
        # This is a placeholder. You'll need to handle actual texture import
        image = bpy.data.images.new(name=texture_data.gltf_name or 'Imported Texture', width=1024, height=1024)
        self.uuid_to_object[texture_data.vircadia_uuid] = image
        return image

    def import_image(self, image_data: TableImage) -> bpy.types.Image:
        # This is a placeholder. You'll need to handle actual image import
        image = bpy.data.images.new(name=image_data.gltf_name or 'Imported Image', width=1024, height=1024)
        self.uuid_to_object[image_data.vircadia_uuid] = image
        return image

    def import_sampler(self, sampler_data: TableSampler) -> None:
        # Samplers in glTF correspond to texture settings in Blender
        # You might not need to create a separate Blender object for this
        pass

    def import_animation(self, animation_data: TableAnimation) -> bpy.types.Action:
        action = bpy.data.actions.new(name=animation_data.gltf_name or 'Imported Animation')
        self.uuid_to_object[animation_data.vircadia_uuid] = action
        
        # Import animation data
        for channel in animation_data.gltf_channels or []:
            # Create F-curves and keyframes based on channel data
            pass
        
        return action

    def import_skin(self, skin_data: TableSkin) -> bpy.types.Object:
        armature = bpy.data.armatures.new(name=skin_data.gltf_name or 'Imported Armature')
        obj = bpy.data.objects.new(skin_data.gltf_name or 'Imported Armature', armature)
        self.uuid_to_object[skin_data.vircadia_uuid] = obj
        
        # Import joint hierarchy and inverse bind matrices
        
        if bpy.context:
            bpy.context.scene.collection.objects.link(obj)

        return obj

    def import_camera(self, camera_data: TableCamera) -> bpy.types.Object:
        camera = bpy.data.cameras.new(name=camera_data.gltf_name or 'Imported Camera')
        obj = bpy.data.objects.new(camera_data.gltf_name or 'Imported Camera', camera)
        self.uuid_to_object[camera_data.vircadia_uuid] = obj
        
        if camera_data.gltf_type == 'perspective':
            camera.type = 'PERSP'
            if camera_data.gltf_perspective:
                persp = camera_data.gltf_perspective
                camera.angle = persp.get('yfov', 0.7853981633974483)  # Default to 45 degrees
                camera.clip_start = persp.get('znear', 0.1)
                camera.clip_end = persp.get('zfar', 100)
        elif camera_data.gltf_type == 'orthographic':
            camera.type = 'ORTHO'
            if camera_data.gltf_orthographic:
                ortho = camera_data.gltf_orthographic
                camera.ortho_scale = max(ortho.get('xmag', 1), ortho.get('ymag', 1)) * 2
                camera.clip_start = ortho.get('znear', 0.1)
                camera.clip_end = ortho.get('zfar', 100)
        
        if bpy.context:
            bpy.context.scene.collection.objects.link(obj)
        return obj

    def import_buffer(self, buffer_data: TableBuffer) -> None:
        # Buffers in glTF are typically binary data
        # You might not need to create a separate Blender object for this
        pass

    def import_buffer_view(self, buffer_view_data: TableBufferView) -> None:
        # Buffer views in glTF are typically slices of buffers
        # You might not need to create a separate Blender object for this
        pass

    def import_accessor(self, accessor_data: TableAccessor) -> None:
        # Accessors in glTF define how to interpret buffer data
        # You might not need to create a separate Blender object for this
        pass

    def set_parent(self, child_uuid: str, parent_uuid: str) -> None:
        child_obj = self.uuid_to_object.get(child_uuid)
        parent_obj = self.uuid_to_object.get(parent_uuid)
        if isinstance(child_obj, bpy.types.Object) and isinstance(parent_obj, bpy.types.Object):
            child_obj.parent = parent_obj

    def assign_material_to_mesh(self, mesh_uuid: str, material_uuid: str) -> None:
        mesh_obj = self.uuid_to_object.get(mesh_uuid)
        material = self.uuid_to_object.get(material_uuid)
        if isinstance(mesh_obj, bpy.types.Object) and mesh_obj.type == 'MESH' and isinstance(material, bpy.types.Material):
            if mesh_obj.data.materials:
                mesh_obj.data.materials[0] = material
            else:
                mesh_obj.data.materials.append(material)

    def assign_texture_to_material(self, material_uuid: str, texture_uuid: str, texture_type: str) -> None:
        material = self.uuid_to_object.get(material_uuid)
        texture = self.uuid_to_object.get(texture_uuid)
        if isinstance(material, bpy.types.Material) and isinstance(texture, bpy.types.Image):
            # Assign texture to appropriate slot in material node tree
            pass

    def get_object_by_uuid(self, uuid: str) -> Optional[bpy.types.ID]:
        return self.uuid_to_object.get(uuid)