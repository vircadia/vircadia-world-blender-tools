import bpy
import bmesh

def get_lightmap_settings(scene):
    return {
        'color_space': scene.vircadia_lightmap_color_space,
        'texel_density': scene.vircadia_lightmap_texel_density,
        'min_resolution': scene.vircadia_lightmap_min_resolution,
        'max_resolution': scene.vircadia_lightmap_max_resolution,
        'factor_shared_materials': scene.vircadia_lightmap_factor_shared_materials,
        'unwrap_context': scene.vircadia_lightmap_unwrap_context,
        'margin': scene.vircadia_lightmap_margin,
        'uv_type': scene.vircadia_lightmap_uv_type,
        'automatic_grouping': scene.vircadia_lightmap_automatic_grouping
    }

def get_bake_settings(scene):
    return {
        'bake_type': scene.vircadia_lightmap_bake_type,
        'use_pass_direct': scene.vircadia_lightmap_use_pass_direct,
        'use_pass_indirect': scene.vircadia_lightmap_use_pass_indirect,
        'use_pass_color': scene.vircadia_lightmap_use_pass_color,
        'use_clear': scene.vircadia_lightmap_use_clear,
        'use_adaptive_sampling': scene.vircadia_lightmap_use_adaptive_sampling,
        'adaptive_threshold': scene.vircadia_lightmap_adaptive_threshold,
        'samples': scene.vircadia_lightmap_samples,
        'adaptive_min_samples': scene.vircadia_lightmap_adaptive_min_samples,
        'use_denoising': scene.vircadia_lightmap_use_denoising,
        'denoiser': scene.vircadia_lightmap_denoiser,
        'denoising_input_passes': scene.vircadia_lightmap_denoising_input_passes,
        'bake_margin': scene.vircadia_lightmap_bake_margin
    }

def setup_bake_settings(scene):
    bake_settings = get_bake_settings(scene)
    
    # Set up bake settings
    scene.cycles.bake_type = bake_settings['bake_type']
    scene.render.bake.use_pass_direct = bake_settings['use_pass_direct']
    scene.render.bake.use_pass_indirect = bake_settings['use_pass_indirect']
    scene.render.bake.use_pass_color = bake_settings['use_pass_color']
    scene.render.bake.use_clear = bake_settings['use_clear']
    scene.cycles.use_adaptive_sampling = bake_settings['use_adaptive_sampling']
    scene.cycles.adaptive_threshold = bake_settings['adaptive_threshold']
    scene.cycles.samples = bake_settings['samples']
    scene.cycles.adaptive_min_samples = bake_settings['adaptive_min_samples']
    scene.cycles.use_denoising = bake_settings['use_denoising']
    scene.cycles.denoiser = bake_settings['denoiser']
    scene.cycles.denoising_input_passes = bake_settings['denoising_input_passes']
    scene.render.bake.margin = bake_settings['bake_margin']

def apply_bake_settings(settings):
    for setting, value in settings.items():
        if setting.startswith('use_') or setting == 'bake_type':
            setattr(bpy.context.scene.cycles, setting, value)
        elif setting in ['use_pass_direct', 'use_pass_indirect', 'use_pass_color', 'use_clear', 'margin']:
            setattr(bpy.context.scene.render.bake, setting, value)
        else:
            setattr(bpy.context.scene.cycles, setting, value)

def calculate_total_surface_area(objects):
    total_area = 0.0
    for obj in objects:
        if obj.type == 'MESH':
            bm = bmesh.new()
            bm.from_mesh(obj.data)
            bm.transform(obj.matrix_world)
            total_area += sum(f.calc_area() for f in bm.faces)
            bm.free()
    return total_area

def determine_shared_resolution(total_surface_area, texel_density, min_res, max_res):
    required_resolution = int((total_surface_area ** 0.5) * texel_density)
    # Round to the nearest power of two within min and max bounds
    resolution = 2 ** (required_resolution - 1).bit_length()
    resolution = max(min_res, min(resolution, max_res))
    return resolution