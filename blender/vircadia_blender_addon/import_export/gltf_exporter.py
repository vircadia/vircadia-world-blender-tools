import bpy
import os

def export_gltf(context, filepath):
    file_ext = os.path.splitext(filepath)[1].lower()
    if file_ext not in ['.gltf', '.glb']:
        filepath = filepath + '.glb'

    export_settings = {
        'export_format': 'GLB' if filepath.lower().endswith('.glb') else 'GLTF_SEPARATE',
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
        'export_texture_dir': os.path.dirname(filepath),
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
