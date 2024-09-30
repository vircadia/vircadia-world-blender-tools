import os
from supabase import create_client, Client
from typing import Dict, Any, List, Optional
import json
import bpy
import mathutils
import uuid
from datetime import datetime
from jsonpatch import JsonPatch
from ..vircadia_world_meta.python.meta import (
    World_WorldGLTF, World_Scene, World_Node, World_Mesh, World_Material,
    World_Texture, World_Image, World_Sampler, World_Animation, World_Skin,
    World_Camera, World_Buffer, World_BufferView, World_Accessor,
    World_Table, World_RealtimeBroadcastChannel, World_RealtimePresenceChannel,
    World_BabylonJS, World_LOD, World_Billboard, World_Lightmap,
    World_CommonEntityProperties, World_BillboardMode,
    Agent_WebRTCSignalType, Agent_Presence
)
from io_scene_gltf2.io.exp import gltf2_io_export
from io_scene_gltf2.blender.exp import gltf2_blender_export
import logging
import bmesh
from mathutils import Vector, Quaternion, Matrix

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseError(Exception):
    pass

class WorldManager:
    def __init__(self):
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_ANON_KEY")
        if not url or not key:
            raise SupabaseError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        self.supabase: Client = create_client(url, key)
        self.current_world_id: Optional[str] = None

    def select_world(self, world_id: str):
        result = self.supabase.table('world_gltf').select("*").eq("vircadia_uuid", world_id).execute()
        if result.data:
            self.current_world_id = world_id
        else:
            raise SupabaseError(f"World with id {world_id} not found")

    def get_current_world(self) -> World_WorldGLTF:
        if not self.current_world_id:
            raise SupabaseError("No world selected. Call select_world() first.")
        result = self.supabase.table('world_gltf').select("*").eq("vircadia_uuid", self.current_world_id).execute()
        return World_WorldGLTF(**result.data[0]) if result.data else None

class BlenderToGLTF:
    def __init__(self):
        self.export_settings = gltf2_blender_export.create_default_export_settings()
        self.export_settings['gltf_format'] = 'JSON'
        self.export_settings['use_selection'] = True

    def convert_world(self) -> World_WorldGLTF:
        # Export entire Blender file
        self.export_settings['use_selection'] = False
        glTF = gltf2_io_export.export_gltf(self.export_settings)
        gltf_data = glTF.to_dict()

        # Create World_WorldGLTF object
        world = World_WorldGLTF(
            vircadia_uuid=str(uuid.uuid4()),
            name=bpy.data.filepath,
            version="1.0",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=gltf_data.get('asset', {}),
            defaultScene=gltf_data.get('scene'),
            extensionsUsed=gltf_data.get('extensionsUsed'),
            extensionsRequired=gltf_data.get('extensionsRequired'),
            extensions=gltf_data.get('extensions'),
            extras=World_CommonEntityProperties(
                name=bpy.data.filepath,
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            ),
            asset=gltf_data.get('asset', {})
        )
        return world

    def convert_scene(self, scene: bpy.types.Scene) -> World_Scene:
        # Set the current scene
        bpy.context.window.scene = scene

        # Export the entire scene
        self.export_settings['use_selection'] = False
        glTF = gltf2_io_export.export_gltf(self.export_settings)
        gltf_data = glTF.to_dict()

        # Create World_Scene object
        scene_data = World_Scene(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name=scene.name,
            nodes=[node['name'] for node in gltf_data.get('nodes', [])],
            extensions=gltf_data.get('extensions'),
            extras=World_CommonEntityProperties(
                name=scene.name,
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )
        return scene_data

    def convert_node(self, obj: bpy.types.Object) -> World_Node:
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select only the desired object
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Export to in-memory buffer
        glTF = gltf2_io_export.export_gltf(self.export_settings)
        gltf_data = glTF.to_dict()

        # Assuming the exported data contains only one node (our object)
        node_data = gltf_data['nodes'][0] if 'nodes' in gltf_data else {}

        # Create World_Node object
        node = World_Node(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name=obj.name,
            camera=node_data.get('camera'),
            children=node_data.get('children'),
            skin=node_data.get('skin'),
            matrix=node_data.get('matrix'),
            mesh=node_data.get('mesh'),
            rotation=node_data.get('rotation'),
            scale=node_data.get('scale'),
            translation=node_data.get('translation'),
            weights=node_data.get('weights'),
            extensions=node_data.get('extensions'),
            extras=World_CommonEntityProperties(
                name=obj.name,
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )
        return node

    def convert_mesh(self, obj: bpy.types.Object) -> World_Mesh:
        mesh = obj.data
        primitives = []

        # Create a bmesh from the mesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces)

        # Get vertex data
        vertices = [v.co for v in bm.verts]
        normals = [v.normal for v in bm.verts]
        uvs = []
        if bm.loops.layers.uv:
            uv_layer = bm.loops.layers.uv.active
            uvs = [l[uv_layer].uv for f in bm.faces for l in f.loops]

        # Get face data
        indices = [[l.vert.index for l in f.loops] for f in bm.faces]

        # Create primitive
        primitive = {
            "attributes": {
                "POSITION": self.create_accessor(vertices, "VEC3"),
                "NORMAL": self.create_accessor(normals, "VEC3"),
            },
            "indices": self.create_accessor(indices, "SCALAR", 5125),  # 5125 is UNSIGNED_INT
            "mode": 4  # TRIANGLES
        }

        if uvs:
            primitive["attributes"]["TEXCOORD_0"] = self.create_accessor(uvs, "VEC2")

        primitives.append(primitive)

        bm.free()

        return World_Mesh(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name=obj.name,
            primitives=primitives,
            extras=World_CommonEntityProperties(
                name=obj.name,
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def convert_material(self, material: bpy.types.Material) -> World_Material:
        pbr_metallic_roughness = {}
        if material.use_nodes:
            principled = next((n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            if principled:
                pbr_metallic_roughness = {
                    "baseColorFactor": list(principled.inputs['Base Color'].default_value),
                    "metallicFactor": principled.inputs['Metallic'].default_value,
                    "roughnessFactor": principled.inputs['Roughness'].default_value
                }

        return World_Material(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name=material.name,
            pbrMetallicRoughness=pbr_metallic_roughness,
            doubleSided=material.use_backface_culling,
            alphaMode="OPAQUE" if material.blend_method == 'OPAQUE' else "BLEND",
            extras=World_CommonEntityProperties(
                name=material.name,
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def convert_texture(self, texture: bpy.types.Texture) -> World_Texture:
        return World_Texture(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name=texture.name,
            source=texture.image.name if texture.image else None,
            extras=World_CommonEntityProperties(
                name=texture.name,
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def convert_image(self, image: bpy.types.Image) -> World_Image:
        return World_Image(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name=image.name,
            uri=image.filepath,
            mimeType=f"image/{image.file_format.lower()}",
            extras=World_CommonEntityProperties(
                name=image.name,
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def convert_sampler(self, texture: bpy.types.Texture) -> World_Sampler:
        return World_Sampler(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name=f"{texture.name}_sampler",
            magFilter=9729,  # LINEAR
            minFilter=9987,  # LINEAR_MIPMAP_LINEAR
            wrapS=10497,  # REPEAT
            wrapT=10497,  # REPEAT
            extras=World_CommonEntityProperties(
                name=f"{texture.name}_sampler",
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def convert_animation(self, action: bpy.types.Action) -> World_Animation:
        channels = []
        samplers = []

        for fcurve in action.fcurves:
            sampler = {
                "input": self.create_accessor([k.co[0] for k in fcurve.keyframe_points], "SCALAR"),
                "output": self.create_accessor([k.co[1] for k in fcurve.keyframe_points], "SCALAR"),
                "interpolation": "LINEAR"
            }
            samplers.append(sampler)

            channel = {
                "sampler": len(samplers) - 1,
                "target": {
                    "node": fcurve.data_path.split('"')[1] if '"' in fcurve.data_path else fcurve.data_path,
                    "path": fcurve.data_path.split('.')[-1]
                }
            }
            channels.append(channel)

        return World_Animation(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name=action.name,
            channels=channels,
            samplers=samplers,
            extras=World_CommonEntityProperties(
                name=action.name,
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def convert_skin(self, armature: bpy.types.Armature) -> World_Skin:
        joints = [bone.name for bone in armature.bones]
        inverse_bind_matrices = [bone.matrix_local.inverted() for bone in armature.bones]

        return World_Skin(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name=armature.name,
            inverseBindMatrices=self.create_accessor(inverse_bind_matrices, "MAT4"),
            joints=joints,
            extras=World_CommonEntityProperties(
                name=armature.name,
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def convert_camera(self, camera: bpy.types.Camera) -> World_Camera:
        camera_type = "perspective" if camera.type == 'PERSP' else "orthographic"
        camera_data = {
            "aspectRatio": camera.angle_x / camera.angle_y,
            "yfov": camera.angle_y,
            "zfar": camera.clip_end,
            "znear": camera.clip_start
        } if camera_type == "perspective" else {
            "xmag": camera.ortho_scale / 2,
            "ymag": camera.ortho_scale / 2,
            "zfar": camera.clip_end,
            "znear": camera.clip_start
        }

        return World_Camera(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name=camera.name,
            type=camera_type,
            perspective=camera_data if camera_type == "perspective" else None,
            orthographic=camera_data if camera_type == "orthographic" else None,
            extras=World_CommonEntityProperties(
                name=camera.name,
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def convert_buffer(self, buffer_data: bytes) -> World_Buffer:
        return World_Buffer(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name="buffer",
            byteLength=len(buffer_data),
            data=buffer_data,
            extras=World_CommonEntityProperties(
                name="buffer",
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def convert_buffer_view(self, buffer_view_data: Dict[str, Any]) -> World_BufferView:
        return World_BufferView(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name="bufferView",
            buffer=buffer_view_data['buffer'],
            byteOffset=buffer_view_data.get('byteOffset', 0),
            byteLength=buffer_view_data['byteLength'],
            byteStride=buffer_view_data.get('byteStride'),
            target=buffer_view_data.get('target'),
            extras=World_CommonEntityProperties(
                name="bufferView",
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def convert_accessor(self, accessor_data: Dict[str, Any]) -> World_Accessor:
        return World_Accessor(
            vircadia_uuid=str(uuid.uuid4()),
            vircadia_world_uuid=str(uuid.uuid4()),  # This should be set to the actual world UUID
            name="accessor",
            bufferView=accessor_data['bufferView'],
            byteOffset=accessor_data.get('byteOffset', 0),
            componentType=accessor_data['componentType'],
            count=accessor_data['count'],
            type=accessor_data['type'],
            max=accessor_data.get('max'),
            min=accessor_data.get('min'),
            normalized=accessor_data.get('normalized', False),
            sparse=accessor_data.get('sparse'),
            extras=World_CommonEntityProperties(
                name="accessor",
                uuid=str(uuid.uuid4()),
                version="1.0",
                createdAt=datetime.now(),
                updatedAt=datetime.now(),
                babylonjs=World_BabylonJS(
                    lod=World_LOD(),
                    billboard=World_Billboard(),
                    lightmap=World_Lightmap(),
                    script={}
                )
            )
        )

    def create_accessor(self, data, accessor_type, component_type=5126):  # 5126 is FLOAT
        flat_data = [item for sublist in data for item in (sublist if isinstance(sublist, (list, Vector)) else [sublist])]
        buffer = self.convert_buffer(np.array(flat_data, dtype=np.float32).tobytes())
        
        buffer_view = self.convert_buffer_view({
            'buffer': buffer.vircadia_uuid,
            'byteLength': len(buffer.data),
            'target': 34962  # ARRAY_BUFFER
        })

        return self.convert_accessor({
            'bufferView': buffer_view.vircadia_uuid,
            'componentType': component_type,
            'count': len(data),
            'type': accessor_type,
            'max': list(np.max(data, axis=0)) if accessor_type != "SCALAR" else [max(data)],
            'min': list(np.min(data, axis=0)) if accessor_type != "SCALAR" else [min(data)]
        })

    def get_scenes(self) -> List[str]:
        return [scene.name for scene in bpy.data.scenes]

    def get_objects(self) -> List[str]:
        return [obj.name for obj in bpy.data.objects]

    def get_materials(self) -> List[str]:
        return [material.name for material in bpy.data.materials]

    def get_textures(self) -> List[str]:
        return [texture.name for texture in bpy.data.textures]

    def get_images(self) -> List[str]:
        return [image.name for image in bpy.data.images]

    def get_actions(self) -> List[str]:
        return [action.name for action in bpy.data.actions]

    def get_armatures(self) -> List[str]:
        return [armature.name for armature in bpy.data.armatures]

    def get_cameras(self) -> List[str]:
        return [camera.name for camera in bpy.data.cameras]

class SupabaseOperations:
    def __init__(self, world_manager: WorldManager):
        self.world_manager = world_manager
        self.supabase = world_manager.supabase

    def create_node(self, node_data: World_Node) -> Dict:
        if not self.world_manager.current_world_id:
            raise SupabaseError("No world selected. Call select_world() first.")
        node_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_node', node_data.dict()).execute()
        return result.data

    def update_node(self, node_id: str, node_data: World_Node) -> Dict:
        result = self.supabase.rpc('update_node', {
            'p_vircadia_uuid': node_id,
            **node_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_node(self, node_id: str) -> Dict:
        result = self.supabase.rpc('delete_node', {'p_vircadia_uuid': node_id}).execute()
        return result.data

    def get_nodes(self) -> List[World_Node]:
        if not self.world_manager.current_world_id:
            raise SupabaseError("No world selected. Call select_world() first.")
        result = self.supabase.table('nodes').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Node(**node) for node in result.data]

    # CRUD operations for Scene
    def create_scene(self, scene_data: World_Scene) -> Dict:
        scene_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_scene', scene_data.dict()).execute()
        return result.data

    def update_scene(self, scene_id: str, scene_data: World_Scene) -> Dict:
        result = self.supabase.rpc('update_scene', {
            'p_vircadia_uuid': scene_id,
            **scene_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_scene(self, scene_id: str) -> Dict:
        result = self.supabase.rpc('delete_scene', {'p_vircadia_uuid': scene_id}).execute()
        return result.data

    def get_scenes(self) -> List[World_Scene]:
        result = self.supabase.table('scenes').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Scene(**scene) for scene in result.data]

    # CRUD operations for Mesh
    def create_mesh(self, mesh_data: World_Mesh) -> Dict:
        mesh_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_mesh', mesh_data.dict()).execute()
        return result.data

    def update_mesh(self, mesh_id: str, mesh_data: World_Mesh) -> Dict:
        result = self.supabase.rpc('update_mesh', {
            'p_vircadia_uuid': mesh_id,
            **mesh_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_mesh(self, mesh_id: str) -> Dict:
        result = self.supabase.rpc('delete_mesh', {'p_vircadia_uuid': mesh_id}).execute()
        return result.data

    def get_meshes(self) -> List[World_Mesh]:
        result = self.supabase.table('meshes').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Mesh(**mesh) for mesh in result.data]

    # CRUD operations for Material
    def create_material(self, material_data: World_Material) -> Dict:
        material_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_material', material_data.dict()).execute()
        return result.data

    def update_material(self, material_id: str, material_data: World_Material) -> Dict:
        result = self.supabase.rpc('update_material', {
            'p_vircadia_uuid': material_id,
            **material_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_material(self, material_id: str) -> Dict:
        result = self.supabase.rpc('delete_material', {'p_vircadia_uuid': material_id}).execute()
        return result.data

    def get_materials(self) -> List[World_Material]:
        result = self.supabase.table('materials').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Material(**material) for material in result.data]

    # CRUD operations for Texture
    def create_texture(self, texture_data: World_Texture) -> Dict:
        texture_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_texture', texture_data.dict()).execute()
        return result.data

    def update_texture(self, texture_id: str, texture_data: World_Texture) -> Dict:
        result = self.supabase.rpc('update_texture', {
            'p_vircadia_uuid': texture_id,
            **texture_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_texture(self, texture_id: str) -> Dict:
        result = self.supabase.rpc('delete_texture', {'p_vircadia_uuid': texture_id}).execute()
        return result.data

    def get_textures(self) -> List[World_Texture]:
        result = self.supabase.table('textures').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Texture(**texture) for texture in result.data]

    # CRUD operations for Image
    def create_image(self, image_data: World_Image) -> Dict:
        image_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_image', image_data.dict()).execute()
        return result.data

    def update_image(self, image_id: str, image_data: World_Image) -> Dict:
        result = self.supabase.rpc('update_image', {
            'p_vircadia_uuid': image_id,
            **image_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_image(self, image_id: str) -> Dict:
        result = self.supabase.rpc('delete_image', {'p_vircadia_uuid': image_id}).execute()
        return result.data

    def get_images(self) -> List[World_Image]:
        result = self.supabase.table('images').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Image(**image) for image in result.data]

    # CRUD operations for Sampler
    def create_sampler(self, sampler_data: World_Sampler) -> Dict:
        sampler_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_sampler', sampler_data.dict()).execute()
        return result.data

    def update_sampler(self, sampler_id: str, sampler_data: World_Sampler) -> Dict:
        result = self.supabase.rpc('update_sampler', {
            'p_vircadia_uuid': sampler_id,
            **sampler_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_sampler(self, sampler_id: str) -> Dict:
        result = self.supabase.rpc('delete_sampler', {'p_vircadia_uuid': sampler_id}).execute()
        return result.data

    def get_samplers(self) -> List[World_Sampler]:
        result = self.supabase.table('samplers').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Sampler(**sampler) for sampler in result.data]

    # CRUD operations for Animation
    def create_animation(self, animation_data: World_Animation) -> Dict:
        animation_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_animation', animation_data.dict()).execute()
        return result.data

    def update_animation(self, animation_id: str, animation_data: World_Animation) -> Dict:
        result = self.supabase.rpc('update_animation', {
            'p_vircadia_uuid': animation_id,
            **animation_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_animation(self, animation_id: str) -> Dict:
        result = self.supabase.rpc('delete_animation', {'p_vircadia_uuid': animation_id}).execute()
        return result.data

    def get_animations(self) -> List[World_Animation]:
        result = self.supabase.table('animations').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Animation(**animation) for animation in result.data]

    # CRUD operations for Skin
    def create_skin(self, skin_data: World_Skin) -> Dict:
        skin_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_skin', skin_data.dict()).execute()
        return result.data

    def update_skin(self, skin_id: str, skin_data: World_Skin) -> Dict:
        result = self.supabase.rpc('update_skin', {
            'p_vircadia_uuid': skin_id,
            **skin_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_skin(self, skin_id: str) -> Dict:
        result = self.supabase.rpc('delete_skin', {'p_vircadia_uuid': skin_id}).execute()
        return result.data

    def get_skins(self) -> List[World_Skin]:
        result = self.supabase.table('skins').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Skin(**skin) for skin in result.data]

    # CRUD operations for Camera
    def create_camera(self, camera_data: World_Camera) -> Dict:
        camera_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_camera', camera_data.dict()).execute()
        return result.data

    def update_camera(self, camera_id: str, camera_data: World_Camera) -> Dict:
        result = self.supabase.rpc('update_camera', {
            'p_vircadia_uuid': camera_id,
            **camera_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_camera(self, camera_id: str) -> Dict:
        result = self.supabase.rpc('delete_camera', {'p_vircadia_uuid': camera_id}).execute()
        return result.data

    def get_cameras(self) -> List[World_Camera]:
        result = self.supabase.table('cameras').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Camera(**camera) for camera in result.data]

    # CRUD operations for Buffer
    def create_buffer(self, buffer_data: World_Buffer) -> Dict:
        buffer_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_buffer', buffer_data.dict()).execute()
        return result.data

    def update_buffer(self, buffer_id: str, buffer_data: World_Buffer) -> Dict:
        result = self.supabase.rpc('update_buffer', {
            'p_vircadia_uuid': buffer_id,
            **buffer_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_buffer(self, buffer_id: str) -> Dict:
        result = self.supabase.rpc('delete_buffer', {'p_vircadia_uuid': buffer_id}).execute()
        return result.data

    def get_buffers(self) -> List[World_Buffer]:
        result = self.supabase.table('buffers').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Buffer(**buffer) for buffer in result.data]

    # CRUD operations for BufferView
    def create_buffer_view(self, buffer_view_data: World_BufferView) -> Dict:
        buffer_view_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_buffer_view', buffer_view_data.dict()).execute()
        return result.data

    def update_buffer_view(self, buffer_view_id: str, buffer_view_data: World_BufferView) -> Dict:
        result = self.supabase.rpc('update_buffer_view', {
            'p_vircadia_uuid': buffer_view_id,
            **buffer_view_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_buffer_view(self, buffer_view_id: str) -> Dict:
        result = self.supabase.rpc('delete_buffer_view', {'p_vircadia_uuid': buffer_view_id}).execute()
        return result.data

    def get_buffer_views(self) -> List[World_BufferView]:
        result = self.supabase.table('buffer_views').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_BufferView(**buffer_view) for buffer_view in result.data]

    # CRUD operations for Accessor
    def create_accessor(self, accessor_data: World_Accessor) -> Dict:
        accessor_data.vircadia_world_uuid = self.world_manager.current_world_id
        result = self.supabase.rpc('create_accessor', accessor_data.dict()).execute()
        return result.data

    def update_accessor(self, accessor_id: str, accessor_data: World_Accessor) -> Dict:
        result = self.supabase.rpc('update_accessor', {
            'p_vircadia_uuid': accessor_id,
            **accessor_data.dict(exclude={'vircadia_uuid', 'vircadia_world_uuid'})
        }).execute()
        return result.data

    def delete_accessor(self, accessor_id: str) -> Dict:
        result = self.supabase.rpc('delete_accessor', {'p_vircadia_uuid': accessor_id}).execute()
        return result.data

    def get_accessors(self) -> List[World_Accessor]:
        result = self.supabase.table('accessors').select("*").eq("vircadia_world_uuid", self.world_manager.current_world_id).execute()
        return [World_Accessor(**accessor) for accessor in result.data]

    def setup_realtime_subscriptions(self, callback):
        for table in World_Table:
            self.supabase.table(table.value).on('*', callback).subscribe()

class GLTFToBlender:
    def __init__(self):
        self.world_manager = None

    def set_world_manager(self, world_manager):
        self.world_manager = world_manager

    def convert_world(self, world: World_WorldGLTF):
        # Clear existing scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()

        # Create a new scene
        scene = bpy.data.scenes.new(name=world.name)
        bpy.context.window.scene = scene

        # Set world properties
        self.set_world_properties(world)

        # Convert and add all entities
        self.convert_scenes()
        self.convert_nodes()
        self.convert_meshes()
        self.convert_materials()
        self.convert_textures()
        self.convert_images()
        self.convert_samplers()
        self.convert_animations()
        self.convert_skins()
        self.convert_cameras()
        self.convert_buffers()
        self.convert_buffer_views()
        self.convert_accessors()

    def set_world_properties(self, world: World_WorldGLTF):
        scene = bpy.context.scene
        scene.name = world.name
        # Set other world properties as needed
        if world.extras and world.extras.babylonjs:
            babylonjs = world.extras.babylonjs
            # Set BabylonJS specific properties if needed

    def convert_scenes(self):
        scenes = self.world_manager.supabase_ops.get_scenes()
        for scene_data in scenes:
            scene = bpy.data.scenes.new(name=scene_data.name)
            self.set_scene_properties(scene, scene_data)

    def set_scene_properties(self, scene: bpy.types.Scene, scene_data: World_Scene):
        if scene_data.extras and scene_data.extras.babylonjs:
            babylonjs = scene_data.extras.babylonjs
            if babylonjs.clearColor:
                scene.world.node_tree.nodes["Background"].inputs[0].default_value = (
                    babylonjs.clearColor.r,
                    babylonjs.clearColor.g,
                    babylonjs.clearColor.b,
                    1  # Alpha
                )
            if babylonjs.gravity:
                scene.gravity = (babylonjs.gravity.x, babylonjs.gravity.y, babylonjs.gravity.z)
            # Set other scene properties
            scene.render.use_motion_blur = babylonjs.autoAnimate or False
            scene.frame_start = babylonjs.autoAnimateFrom or 0
            scene.frame_end = babylonjs.autoAnimateTo or 100
            scene.render.fps = babylonjs.autoAnimateSpeed or 24

    def convert_nodes(self):
        nodes = self.world_manager.supabase_ops.get_nodes()
        for node_data in nodes:
            obj = bpy.data.objects.new(node_data.name, None)
            bpy.context.scene.collection.objects.link(obj)
            self.set_node_properties(obj, node_data)

    def set_node_properties(self, obj: bpy.types.Object, node_data: World_Node):
        if node_data.translation:
            obj.location = Vector(node_data.translation)
        if node_data.rotation:
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = Quaternion(node_data.rotation)
        if node_data.scale:
            obj.scale = Vector(node_data.scale)
        if node_data.matrix:
            obj.matrix_world = Matrix(node_data.matrix)

        if node_data.extras and node_data.extras.babylonjs:
            babylonjs = node_data.extras.babylonjs
            if babylonjs.billboard and babylonjs.billboard.mode is not None:
                constraint = obj.constraints.new(type='TRACK_TO')
                constraint.target = bpy.context.scene.camera
                constraint.track_axis = 'TRACK_NEGATIVE_Z'
                constraint.up_axis = 'UP_Y'

    def convert_meshes(self):
        meshes = self.world_manager.supabase_ops.get_meshes()
        for mesh_data in meshes:
            mesh = bpy.data.meshes.new(name=mesh_data.name)
            obj = bpy.data.objects.new(mesh_data.name, mesh)
            bpy.context.scene.collection.objects.link(obj)
            self.set_mesh_properties(obj, mesh, mesh_data)

    def set_mesh_properties(self, obj: bpy.types.Object, mesh: bpy.types.Mesh, mesh_data: World_Mesh):
        bm = bmesh.new()
        for primitive in mesh_data.primitives:
            # Add vertices
            for i in range(0, len(primitive['attributes']['POSITION']), 3):
                bm.verts.new(primitive['attributes']['POSITION'][i:i+3])
            bm.verts.ensure_lookup_table()

            # Add faces
            for i in range(0, len(primitive['indices']), 3):
                try:
                    bm.faces.new([bm.verts[idx] for idx in primitive['indices'][i:i+3]])
                except ValueError:
                    pass  # Skip invalid face

            # Add normals
            if 'NORMAL' in primitive['attributes']:
                for i, v in enumerate(bm.verts):
                    v.normal = primitive['attributes']['NORMAL'][i*3:(i+1)*3]

            # Add UVs
            if 'TEXCOORD_0' in primitive['attributes']:
                uv_layer = bm.loops.layers.uv.new()
                for face in bm.faces:
                    for loop in face.loops:
                        loop[uv_layer].uv = primitive['attributes']['TEXCOORD_0'][loop.vert.index*2:(loop.vert.index+1)*2]

        bm.to_mesh(mesh)
        bm.free()
        mesh.update()

        if mesh_data.extras and mesh_data.extras.babylonjs:
            babylonjs = mesh_data.extras.babylonjs
            # Set BabylonJS specific properties for mesh if needed

    def convert_materials(self):
        materials = self.world_manager.supabase_ops.get_materials()
        for material_data in materials:
            mat = bpy.data.materials.new(name=material_data.name)
            self.set_material_properties(mat, material_data)

    def set_material_properties(self, mat: bpy.types.Material, material_data: World_Material):
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        principled = nodes["Principled BSDF"]

        if material_data.pbrMetallicRoughness:
            pbr = material_data.pbrMetallicRoughness
            if 'baseColorFactor' in pbr:
                principled.inputs['Base Color'].default_value = pbr['baseColorFactor']
            if 'metallicFactor' in pbr:
                principled.inputs['Metallic'].default_value = pbr['metallicFactor']
            if 'roughnessFactor' in pbr:
                principled.inputs['Roughness'].default_value = pbr['roughnessFactor']

        # Handle other material properties (normal map, occlusion, etc.)
        if material_data.normalTexture:
            # Add normal map node and connect
            pass

        if material_data.occlusionTexture:
            # Add occlusion map node and connect
            pass

        if material_data.emissiveTexture or material_data.emissiveFactor:
            # Add emission node and connect
            pass

        mat.blend_method = material_data.alphaMode or 'OPAQUE'
        mat.alpha_threshold = material_data.alphaCutoff or 0.5
        mat.use_backface_culling = not (material_data.doubleSided or False)

    def convert_textures(self):
        textures = self.world_manager.supabase_ops.get_textures()
        for texture_data in textures:
            # In Blender, textures are usually handled through material nodes
            # We might need to store this information to use when setting up material nodes
            pass

    def convert_images(self):
        images = self.world_manager.supabase_ops.get_images()
        for image_data in images:
            if image_data.uri:
                bpy.data.images.load(image_data.uri)
            elif image_data.bufferView:
                # Handle embedded images
                pass

    def convert_samplers(self):
        samplers = self.world_manager.supabase_ops.get_samplers()
        for sampler_data in samplers:
            # Blender doesn't have a direct equivalent to glTF samplers
            # We might need to store this information to use when setting up material nodes
            pass

    def convert_animations(self):
        animations = self.world_manager.supabase_ops.get_animations()
        for animation_data in animations:
            action = bpy.data.actions.new(name=animation_data.name)
            for channel in animation_data.channels:
                # Create F-Curves and keyframes based on channel data
                pass

    def convert_skins(self):
        skins = self.world_manager.supabase_ops.get_skins()
        for skin_data in skins:
            armature = bpy.data.armatures.new(name=skin_data.name)
            obj = bpy.data.objects.new(skin_data.name, armature)
            bpy.context.scene.collection.objects.link(obj)

            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')

            for joint in skin_data.joints:
                bone = armature.edit_bones.new(name=joint)
                # Set bone properties (head, tail, roll) based on joint data

            bpy.ops.object.mode_set(mode='OBJECT')

    def convert_cameras(self):
        cameras = self.world_manager.supabase_ops.get_cameras()
        for camera_data in cameras:
            cam = bpy.data.cameras.new(name=camera_data.name)
            obj = bpy.data.objects.new(camera_data.name, cam)
            bpy.context.scene.collection.objects.link(obj)

            if camera_data.type == 'perspective':
                cam.type = 'PERSP'
                if camera_data.perspective:
                    cam.angle = camera_data.perspective.yfov
                    cam.clip_start = camera_data.perspective.znear
                    cam.clip_end = camera_data.perspective.zfar
            elif camera_data.type == 'orthographic':
                cam.type = 'ORTHO'
                if camera_data.orthographic:
                    cam.ortho_scale = max(camera_data.orthographic.xmag, camera_data.orthographic.ymag) * 2
                    cam.clip_start = camera_data.orthographic.znear
                    cam.clip_end = camera_data.orthographic.zfar

    def convert_buffers(self):
        buffers = self.world_manager.supabase_ops.get_buffers()
        for buffer_data in buffers:
            # Buffers in glTF are usually binary data
            # We might need to store this data for use in other conversions (e.g., for accessors)
            pass

    def convert_buffer_views(self):
        buffer_views = self.world_manager.supabase_ops.get_buffer_views()
        for buffer_view_data in buffer_views:
            # Buffer views in glTF define sections of buffers
            # We might need to store this information for use in other conversions (e.g., for accessors)
            pass

    def convert_accessors(self):
        accessors = self.world_manager.supabase_ops.get_accessors()
        for accessor_data in accessors:
            # Accessors in glTF define how to interpret buffer data
            # We might need to use this information when creating meshes, animations, etc.
            pass

class BlenderSupabaseSync:
    def __init__(self, world_manager: WorldManager):
        self.world_manager = world_manager
        self.supabase_ops = SupabaseOperations(world_manager)
        self.blender_to_gltf = BlenderToGLTF()
        self.gltf_to_blender = GLTFToBlender()
        self.gltf_to_blender.set_world_manager(world_manager)

    def sync_object(self, blender_object: Any) -> Dict:
        gltf_data = self.blender_to_gltf.convert_node(blender_object)
        return self.supabase_ops.create_node(gltf_data)

    def handle_realtime_update(self, payload):
        logger.info(f'Realtime update received: {payload}')
        # TODO: Implement Blender update logic here

    def partial_update(self, node_id: str, current_data: World_Node, new_data: World_Node):
        patch = JsonPatch.from_diff(current_data.dict(), new_data.dict())
        if patch:
            self.supabase_ops.update_node(node_id, new_data)

    def sync_from_supabase(self):
        world = self.world_manager.get_current_world()
        if world:
            self.gltf_to_blender.convert_world(world)
        else:
            logger.error("No world selected or world not found")

# Usage example
if __name__ == "__main__":
    try:
        world_manager = WorldManager()
        world_manager.select_world("example_world_id")

        sync_manager = BlenderSupabaseSync(world_manager)
        sync_manager.supabase_ops.setup_realtime_subscriptions(sync_manager.handle_realtime_update)

        # Example: Sync a Blender object (replace with actual Blender object)
        class MockBlenderObject:
            def __init__(self, name):
                self.name = name
                self.id_data = "mock_id"

        mock_object = MockBlenderObject("ExampleObject")
        result = sync_manager.sync_object(mock_object)
        logger.info(f"Sync result: {result}")

        # Example: Get all nodes
        nodes = sync_manager.supabase_ops.get_nodes()
        logger.info(f"All nodes: {json.dumps([node.dict() for node in nodes], indent=2)}")

    except SupabaseError as e:
        logger.error(f"Supabase error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)

# TODO: Implement unit tests for each class and method
# TODO: Implement Blender-specific logic for updating objects based on realtime data