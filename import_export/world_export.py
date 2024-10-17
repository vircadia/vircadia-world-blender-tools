import bpy
import uuid
from typing import List, Dict, Any
from datetime import datetime
from ..vircadia_world_sdk_py.shared.modules.vircadia_world_meta.python.world import (
    TableWorldGLTF, TableScene, TableNode, TableMesh, TableMaterial,
    TableTexture, TableImage, TableSampler, TableAnimation, TableSkin,
    TableCamera, TableBuffer, TableBufferView, TableAccessor,
    Vector3, Color3
)

class BlenderToWorldGLTFExport:
    def __init__(self):
        self.world_uuid = str(uuid.uuid4())
        self.object_uuid_map = {}

    def generate_uuid(self, obj):
        if obj not in self.object_uuid_map:
            self.object_uuid_map[obj] = str(uuid.uuid4())
        return self.object_uuid_map[obj]

    def export_world_gltf(self, name: str) -> TableWorldGLTF:
        return TableWorldGLTF(
            vircadia_uuid=self.world_uuid,
            vircadia_version="1.0",
            vircadia_createdat=datetime.now(),
            vircadia_updatedat=datetime.now(),
            vircadia_name=name,
            gltf_asset={"version": "2.0"},
            gltf_scene=0
        )

    def export_scene(self, scene: bpy.types.Scene) -> TableScene:
        return TableScene(
            vircadia_uuid=self.generate_uuid(scene),
            vircadia_world_uuid=self.world_uuid,
            gltf_nodes=[self.generate_uuid(obj) for obj in scene.objects],
            vircadia_babylonjs_scene_clearColor=Color3(*scene.world.node_tree.nodes["Background"].inputs[0].default_value[:3]),
            vircadia_babylonjs_scene_gravity=Vector3(*scene.gravity),
            vircadia_babylonjs_scene_physicsEnabled=scene.use_gravity
        )

    def export_node(self, obj: bpy.types.Object) -> TableNode:
        return TableNode(
            vircadia_uuid=self.generate_uuid(obj),
            vircadia_world_uuid=self.world_uuid,
            gltf_name=obj.name,
            gltf_mesh=self.generate_uuid(obj.data) if obj.type == 'MESH' else None,
            gltf_camera=self.generate_uuid(obj.data) if obj.type == 'CAMERA' else None,
            gltf_children=[self.generate_uuid(child) for child in obj.children],
            gltf_matrix=list(sum([list(row) for row in obj.matrix_world], []))
        )

    def export_mesh(self, mesh: bpy.types.Mesh) -> TableMesh:
        return TableMesh(
            vircadia_uuid=self.generate_uuid(mesh),
            vircadia_world_uuid=self.world_uuid,
            gltf_name=mesh.name,
            gltf_primitives=[{"attributes": {}, "material": self.generate_uuid(mat) if mat else None} for mat in mesh.materials]
        )

    def export_material(self, material: bpy.types.Material) -> TableMaterial:
        return TableMaterial(
            vircadia_uuid=self.generate_uuid(material),
            vircadia_world_uuid=self.world_uuid,
            gltf_name=material.name,
            gltf_pbrMetallicRoughness={
                "baseColorFactor": list(material.diffuse_color),
                "metallicFactor": material.metallic,
                "roughnessFactor": material.roughness
            }
        )

    def export_texture(self, texture: bpy.types.Texture) -> TableTexture:
        return TableTexture(
            vircadia_uuid=self.generate_uuid(texture),
            vircadia_world_uuid=self.world_uuid,
            gltf_name=texture.name,
            gltf_source=self.generate_uuid(texture.image) if texture.image else None
        )

    def export_image(self, image: bpy.types.Image) -> TableImage:
        return TableImage(
            vircadia_uuid=self.generate_uuid(image),
            vircadia_world_uuid=self.world_uuid,
            gltf_name=image.name,
            gltf_uri=image.filepath,
            gltf_mimeType=f"image/{image.file_format.lower()}"
        )

    def export_camera(self, camera: bpy.types.Camera) -> TableCamera:
        return TableCamera(
            vircadia_uuid=self.generate_uuid(camera),
            vircadia_world_uuid=self.world_uuid,
            gltf_name=camera.name,
            gltf_type="perspective" if camera.type == 'PERSP' else "orthographic",
            gltf_perspective={
                "aspectRatio": camera.angle_x / camera.angle_y,
                "yfov": camera.angle_y,
                "zfar": camera.clip_end,
                "znear": camera.clip_start
            } if camera.type == 'PERSP' else None,
            gltf_orthographic={
                "xmag": camera.ortho_scale / 2,
                "ymag": camera.ortho_scale / 2,
                "zfar": camera.clip_end,
                "znear": camera.clip_start
            } if camera.type == 'ORTHO' else None
        )

    def export_all(self, scene: bpy.types.Scene) -> Dict[str, List[Any]]:
        world_gltf = self.export_world_gltf(scene.name)
        exported_scene = self.export_scene(scene)
        
        nodes = [self.export_node(obj) for obj in scene.objects]
        meshes = [self.export_mesh(obj.data) for obj in scene.objects if obj.type == 'MESH']
        materials = [self.export_material(mat) for mat in bpy.data.materials]
        textures = [self.export_texture(tex) for tex in bpy.data.textures]
        images = [self.export_image(img) for img in bpy.data.images]
        cameras = [self.export_camera(obj.data) for obj in scene.objects if obj.type == 'CAMERA']

        return {
            "world_gltf": [world_gltf],
            "scenes": [exported_scene],
            "nodes": nodes,
            "meshes": meshes,
            "materials": materials,
            "textures": textures,
            "images": images,
            "cameras": cameras
        }

def register():
    pass

def unregister():
    pass

