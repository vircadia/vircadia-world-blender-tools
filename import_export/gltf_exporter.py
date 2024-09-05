import bpy
import os
from .. import config
from ..utils import visibility_utils

def export_glb(context, filepath):
    print(f"Starting GLB export to {filepath}")
    directory = os.path.dirname(filepath)
    filename = config.DEFAULT_GLB_EXPORT_FILENAME
    filepath = os.path.join(directory, filename)
    print(f"Full export path: {filepath}")

    export_settings = {
        'export_format': 'GLB',
        'use_selection': False,
    }
    print(f"Export settings: {export_settings}")

    hidden_objects = visibility_utils.temporarily_unhide_objects(context)
    print(f"Temporarily unhidden {len(hidden_objects)} objects")

    try:
        print("Attempting to export GLB...")
        result = bpy.ops.export_scene.gltf(filepath=filepath, **export_settings)
        print(f"Export result: {result}")
        if 'FINISHED' in result:
            print(f"Successfully exported GLB to {filepath}")
            return True
        else:
            print(f"Export failed with result: {result}")
            return False
    except Exception as e:
        print(f"Error exporting GLB: {str(e)}")
        return False
    finally:
        visibility_utils.restore_hidden_objects(hidden_objects)
        print("Restored hidden objects")

    print("GLB export completed.")

def register():
    pass

def unregister():
    pass
