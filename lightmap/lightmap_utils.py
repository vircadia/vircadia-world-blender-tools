import bpy

# Script options
COLOR_SPACE = 'sRGB'
RESOLUTION_SINGLE = 1024
RESOLUTION_SMALL_GROUP = 2048
RESOLUTION_LARGE_GROUP = 4096
SMALL_GROUP_THRESHOLD = 2
LARGE_GROUP_THRESHOLD = 7

# Whitelist for bake settings
BAKE_SETTINGS_WHITELIST = [
    'bake_type',
    'use_pass_direct',
    'use_pass_indirect',
    'use_pass_color',
    'use_clear',
    'use_adaptive_sampling',
    'adaptive_threshold',
    'samples',
    'adaptive_min_samples',
    'use_denoising',
    'denoiser',
    'denoising_input_passes'
]

def setup_bake_settings():
    # Set up bake settings
    bpy.context.scene.cycles.bake_type = 'DIFFUSE'
    bpy.context.scene.render.bake.use_pass_direct = True
    bpy.context.scene.render.bake.use_pass_indirect = True
    bpy.context.scene.render.bake.use_pass_color = False
    bpy.context.scene.render.bake.use_clear = False
    bpy.context.scene.cycles.use_adaptive_sampling = True
    bpy.context.scene.cycles.adaptive_threshold = 0.2
    bpy.context.scene.cycles.samples = 1024
    bpy.context.scene.cycles.adaptive_min_samples = 256
    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.cycles.denoiser = 'OPTIX'
    bpy.context.scene.cycles.denoising_input_passes = 'RGB_ALBEDO'

def get_current_bake_settings():
    settings = {}
    for setting in BAKE_SETTINGS_WHITELIST:
        if setting.startswith('use_') or setting == 'bake_type':
            settings[setting] = getattr(bpy.context.scene.cycles, setting)
        elif setting in ['use_pass_direct', 'use_pass_indirect', 'use_pass_color', 'use_clear']:
            settings[setting] = getattr(bpy.context.scene.render.bake, setting)
        else:
            settings[setting] = getattr(bpy.context.scene.cycles, setting)
    return settings

def apply_bake_settings(settings):
    for setting, value in settings.items():
        if setting.startswith('use_') or setting == 'bake_type':
            setattr(bpy.context.scene.cycles, setting, value)
        elif setting in ['use_pass_direct', 'use_pass_indirect', 'use_pass_color', 'use_clear']:
            setattr(bpy.context.scene.render.bake, setting, value)
        else:
            setattr(bpy.context.scene.cycles, setting, value)