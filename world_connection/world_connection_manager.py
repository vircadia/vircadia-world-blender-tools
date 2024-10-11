from supabase import create_client, Client
from typing import Optional
from ..vircadia_world_sdk_py.shared.modules.vircadia_world_meta.python.world import Table
import bpy
from bpy.app.handlers import persistent

class WorldConnectionManager:
    def __init__(self):
        self.client: Optional[Client] = None
        self.is_connected: bool = False
        self.connection_status: str = "Disconnected"

    def update_status(self, status: str):
        self.connection_status = status
        print(f"Connection status: {status}")
        # for area in bpy.context.screen.areas:
        #     if area.type == 'VIEW_3D':
        #         area.tag_redraw()

    def connect(self, host: str, api_key: str, username: str = "", password: str = ""):
        self.update_status("Connecting...")
        
        try:
            if not host or not api_key:
                raise ValueError("Supabase URL and Key are required")

            self.client = create_client(host, api_key)
            
            if username and password:
                auth_response = self.client.auth.sign_in_with_password({
                    "email": username,
                    "password": password
                })
                if not auth_response.user:
                    raise ValueError("Authentication failed")
            else:
                # Verify connection with a simple query
                self.client.table('connections').select("*").limit(1).execute()

            self.is_connected = True
            self.update_status("Connected")
            self.setup_subscriptions()
        except Exception as e:
            self.update_status(f"Connection error: {str(e)}")
            self.disconnect()

    def disconnect(self):
        self.update_status("Disconnecting...")
        self.is_connected = False
        if self.client:
            self.client.realtime.disconnect()
        self.client = None
        self.update_status("Disconnected")

    def setup_subscriptions(self):
        if not self.client:
            return

        def callback(payload):
            event_type = payload['eventType']
            if event_type == 'INSERT':
                self.handle_insert(payload)
            elif event_type == 'UPDATE':
                self.handle_update(payload)
            elif event_type == 'DELETE':
                self.handle_delete(payload)

        for table in Table:
            channel = self.client.channel(f'table-changes:{table.value}')
            channel.on('postgres_changes', {
                'event': '*',
                'schema': 'public',
                'table': table.value
            }, callback)
            channel.subscribe()

    def handle_insert(self, payload):
        # Handle insert event
        print(f"Insert event: {payload}")

    def handle_update(self, payload):
        # Handle update event
        print(f"Update event: {payload}")

    def handle_delete(self, payload):
        # Handle delete event
        print(f"Delete event: {payload}")

    # Placeholder for import classes
    class WorldGLTFImporter:
        pass

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
    world_connection_manager.disconnect()

bpy.app.handlers.load_post.append(load_handler)