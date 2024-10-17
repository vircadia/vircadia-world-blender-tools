import asyncio
import logging
from supabase._async.client import AsyncClient as Client, create_client
from typing import Optional
from ..vircadia_world_sdk_py.shared.modules.vircadia_world_meta.python.world import Table
import bpy
from bpy.app.handlers import persistent
import json
import tempfile
import os
# from websockets.legacy.exceptions import InvalidStatusCode
# from realtime.exceptions import NotConnectedError

# Enable basic logging
logging.basicConfig(level=logging.INFO)

class WorldConnectionManager:
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected: bool = False
        self.connection_status: str = "Disconnected"

    def update_status(self, status: str):
        self.connection_status = status
        logging.info(f"Connection status: {status}")

    async def connect(self, host: str, api_key: str, username: str = "", password: str = ""):
        self.update_status("Connecting...")
        
        try:
            if not host or not api_key:
                raise ValueError("Supabase URL and Key are required")

            self.client = await create_client(host, api_key)
            
            if username and password:
                auth_response = await self.client.auth.sign_in_with_password({
                    "email": username,
                    "password": password
                })
                if not auth_response.user:
                    raise ValueError("Authentication failed")
            
            # Commented out realtime connection
            # try:
            #     await self.client.realtime.connect()
            # except InvalidStatusCode as e:
            #     if e.status_code == 403:
            #         raise ValueError("WebSocket connection forbidden. Check your Supabase project settings and ensure Realtime is enabled.")
            #     else:
            #         raise
            
            self.is_connected = True
            self.update_status("Connected")
            # await self.setup_subscriptions()
        except Exception as e:
            self.update_status(f"Connection error: {str(e)}")
            await self.disconnect()

    async def disconnect(self):
        self.update_status("Disconnecting...")
        self.is_connected = False
        if self.client:
            try:
                await self.client.auth.sign_out()
            except Exception as e:
                logging.error(f"Error during sign out: {str(e)}")
            
            # Commented out realtime channel removal
            # try:
            #     await self.client.realtime.remove_all_channels()
            # except NotConnectedError:
            #     logging.warning("Realtime client was not connected, skipping channel removal")
            # except Exception as e:
            #     logging.error(f"Error removing channels: {str(e)}")
            
            self.client = None
        self.update_status("Disconnected")

    # Commented out setup_subscriptions method
    # async def setup_subscriptions(self):
    #     if not self.client:
    #         return

    #     async def async_callback(payload):
    #         event_type = payload['eventType']
    #         if event_type == 'INSERT':
    #             await self.handle_insert(payload)
    #         elif event_type == 'UPDATE':
    #             await self.handle_update(payload)
    #         elif event_type == 'DELETE':
    #             await self.handle_delete(payload)

    #     def sync_callback(payload):
    #         asyncio.create_task(async_callback(payload))

    #     for table in Table:
    #         channel = self.client.channel(f'table-changes:{table.value}')
    #         channel.on('postgres_changes',
    #             event='*',  # Listen to all events (INSERT, UPDATE, DELETE)
    #             schema='public',
    #             table=table.value,
    #             callback=sync_callback
    #         )
    #         await channel.subscribe()

    # Commented out event handling methods
    # async def handle_insert(self, payload):
    #     logging.info(f"Insert event: {payload}")

    # async def handle_update(self, payload):
    #     logging.info(f"Update event: {payload}")

    # async def handle_delete(self, payload):
    #     logging.info(f"Delete event: {payload}")

    # Placeholder for import classes
    class WorldGLTFImporter:
        def __init__(self, world_gltf_data):
            self.world_gltf_data = world_gltf_data

        def import_to_blender(self):
            # Reconstruct glTF JSON
            gltf_json = self.reconstruct_gltf_json()

            # Save to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.gltf', delete=False) as temp_file:
                json.dump(gltf_json, temp_file)
                temp_file_path = temp_file.name

            # Import using Blender's glTF importer
            bpy.ops.import_scene.gltf(filepath=temp_file_path)

            # Clean up temporary file
            os.unlink(temp_file_path)

        def reconstruct_gltf_json(self):
            gltf_json = {
                "asset": self.world_gltf_data.gltf_asset,
                "scene": self.world_gltf_data.gltf_scene,
                "scenes": [],  # You'll need to populate this from the scenes table
                "nodes": [],   # Populate from nodes table
                "meshes": [],  # Populate from meshes table
                "materials": [],  # Populate from materials table
                "textures": [],   # Populate from textures table
                "images": [],     # Populate from images table
                "samplers": [],   # Populate from samplers table
                "animations": [], # Populate from animations table
                "skins": [],      # Populate from skins table
                "cameras": [],    # Populate from cameras table
                "buffers": [],    # Populate from buffers table
                "bufferViews": [],  # Populate from buffer_views table
                "accessors": [],    # Populate from accessors table
            }

            if self.world_gltf_data.gltf_extensionsUsed:
                gltf_json["extensionsUsed"] = self.world_gltf_data.gltf_extensionsUsed

            if self.world_gltf_data.gltf_extensionsRequired:
                gltf_json["extensionsRequired"] = self.world_gltf_data.gltf_extensionsRequired

            if self.world_gltf_data.gltf_extensions:
                gltf_json["extensions"] = self.world_gltf_data.gltf_extensions

            if self.world_gltf_data.gltf_extras:
                gltf_json["extras"] = self.world_gltf_data.gltf_extras

            return gltf_json

    class SceneImporter:
        pass

    class NodeImporter:
        pass

    # ... (add placeholders for all other table importers)

    # Placeholder for export classes
    class WorldGLTFExporter:
        pass

    class SceneExporter:
        pass

    class NodeExporter:
        pass

    # ... (add placeholders for all other table exporters)

world_connection_manager = WorldConnectionManager()

@persistent
def load_handler(dummy):
    asyncio.run(world_connection_manager.disconnect())

bpy.app.handlers.load_post.append(load_handler)
