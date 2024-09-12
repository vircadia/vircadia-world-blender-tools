import bpy

def get_lightmap_settings(scene):
    return {
        'color_space': scene.vircadia_lightmap_color_space,
        'resolution_single': scene.vircadia_lightmap_resolution_single,
        'resolution_small': scene.vircadia_lightmap_resolution_small,
        'resolution_large': scene.vircadia_lightmap_resolution_large,
        'small_threshold': scene.vircadia_lightmap_small_threshold,
        'large_threshold': scene.vircadia_lightmap_large_threshold
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
        'denoising_input_passes': scene.vircadia_lightmap_denoising_input_passes
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

def apply_bake_settings(settings):
    for setting, value in settings.items():
        if setting.startswith('use_') or setting == 'bake_type':
            setattr(bpy.context.scene.cycles, setting, value)
        elif setting in ['use_pass_direct', 'use_pass_indirect', 'use_pass_color', 'use_clear']:
            setattr(bpy.context.scene.render.bake, setting, value)
        else:
            setattr(bpy.context.scene.cycles, setting, value)