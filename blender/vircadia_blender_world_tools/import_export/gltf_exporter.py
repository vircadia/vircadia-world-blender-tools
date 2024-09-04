import bpy
import os

def export_gltf(context, filepath):
    # Ensure the filename is 'environment.gltf' or 'environment.glb'
    directory = os.path.dirname(filepath)
    filename = 'environment.glb' if filepath.lower().endswith('.glb') else 'environment.gltf'
    filepath = os.path.join(directory, filename)

    export_settings = {
        'export_format': 'GLB' if filename.lower().endswith('.glb') else 'GLTF_SEPARATE',
        'use_selection': False,
        'export_apply': True,
        'export_animations': True,
        'export_materials': True,
        'export_colors': True,
        'export_normals': True,
        'export_cameras': True,
        'export_lights': True,
        'export_extras': True,
        'export_yup': True,
        'export_texcoords': True,
        'export_nla_strips': True,
        'export_force_sampling': True,
        'export_texture_dir': directory,
        'export_keep_originals': False,
        'export_tangents': False,
        'export_skins': True,
        'export_morph': True,
        'export_bake_animation': False,
        'export_current_frame': False,
        'export_image_format': 'AUTO',
    }

    try:
        bpy.ops.export_scene.gltf(filepath=filepath, **export_settings)
        print(f"Successfully exported GLTF to {filepath}")
    except Exception as e:
        print(f"Error exporting GLTF: {str(e)}")
        return

    print("GLTF export completed.")

def register():
    pass

def unregister():
    pass
