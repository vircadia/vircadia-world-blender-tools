import bpy
from bpy.types import Panel
from ..lightmap import lightmap_utils

class VIRCADIA_PT_lightmap_panel(Panel):
    bl_label = "Lightmap Generation"
    bl_idname = "VIEW3D_PT_vircadia_lightmap"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vircadia"
    bl_parent_id = "VIEW3D_PT_vircadia_main"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Lightmap configuration
        box = layout.box()
        box.label(text="Lightmap Configuration")
        box.prop(scene, "vircadia_lightmap_color_space", text="Color Space")
        box.prop(scene, "vircadia_lightmap_resolution_single", text="Single Resolution")
        box.prop(scene, "vircadia_lightmap_resolution_small", text="Small Group Resolution")
        box.prop(scene, "vircadia_lightmap_resolution_large", text="Large Group Resolution")
        box.prop(scene, "vircadia_lightmap_small_threshold", text="Small Group Threshold")
        box.prop(scene, "vircadia_lightmap_large_threshold", text="Large Group Threshold")

        # Bake settings
        box = layout.box()
        box.label(text="Bake Settings")
        box.prop(scene, "vircadia_lightmap_bake_type", text="Bake Type")
        box.prop(scene, "vircadia_lightmap_use_pass_direct", text="Use Direct")
        box.prop(scene, "vircadia_lightmap_use_pass_indirect", text="Use Indirect")
        box.prop(scene, "vircadia_lightmap_use_pass_color", text="Use Color")
        box.prop(scene, "vircadia_lightmap_use_clear", text="Clear")
        box.prop(scene, "vircadia_lightmap_use_adaptive_sampling", text="Adaptive Sampling")
        box.prop(scene, "vircadia_lightmap_adaptive_threshold", text="Adaptive Threshold")
        box.prop(scene, "vircadia_lightmap_samples", text="Samples")
        box.prop(scene, "vircadia_lightmap_adaptive_min_samples", text="Min Samples")
        box.prop(scene, "vircadia_lightmap_use_denoising", text="Use Denoising")
        box.prop(scene, "vircadia_lightmap_denoiser", text="Denoiser")
        
        if scene.vircadia_lightmap_denoiser == 'OPTIX':
            box.prop(scene, "vircadia_lightmap_denoising_input_passes", text="Passes")
        elif scene.vircadia_lightmap_denoiser == 'OPENIMAGEDENOISE':
            box.prop(scene, "vircadia_lightmap_denoising_input_passes", text="Passes")
            box.prop(scene, "vircadia_lightmap_denoising_prefilter", text="Prefilter")
            box.prop(scene, "vircadia_lightmap_denoising_quality", text="Quality")

        # Generate lightmaps button
        layout.operator("vircadia.generate_lightmaps", text="Generate Lightmaps")

def register():
    bpy.types.Scene.vircadia_lightmap_color_space = bpy.props.StringProperty(
        name="Color Space",
        default="sRGB"
    )
    bpy.types.Scene.vircadia_lightmap_resolution_single = bpy.props.IntProperty(
        name="Single Resolution",
        default=1024,
        min=64,
        max=8192
    )
    bpy.types.Scene.vircadia_lightmap_resolution_small = bpy.props.IntProperty(
        name="Small Group Resolution",
        default=2048,
        min=64,
        max=8192
    )
    bpy.types.Scene.vircadia_lightmap_resolution_large = bpy.props.IntProperty(
        name="Large Group Resolution",
        default=4096,
        min=64,
        max=8192
    )
    bpy.types.Scene.vircadia_lightmap_small_threshold = bpy.props.IntProperty(
        name="Small Group Threshold",
        default=2,
        min=1,
        max=100
    )
    bpy.types.Scene.vircadia_lightmap_large_threshold = bpy.props.IntProperty(
        name="Large Group Threshold",
        default=7,
        min=1,
        max=100
    )

    # Register properties for bake settings
    bpy.types.Scene.vircadia_lightmap_bake_type = bpy.props.EnumProperty(
        name="Bake Type",
        items=[('DIFFUSE', 'Diffuse', 'Bake diffuse lighting')],
        default='DIFFUSE'
    )
    bpy.types.Scene.vircadia_lightmap_use_pass_direct = bpy.props.BoolProperty(
        name="Use Direct",
        default=True
    )
    bpy.types.Scene.vircadia_lightmap_use_pass_indirect = bpy.props.BoolProperty(
        name="Use Indirect",
        default=True
    )
    bpy.types.Scene.vircadia_lightmap_use_pass_color = bpy.props.BoolProperty(
        name="Use Color",
        default=False
    )
    bpy.types.Scene.vircadia_lightmap_use_clear = bpy.props.BoolProperty(
        name="Clear",
        default=False
    )
    bpy.types.Scene.vircadia_lightmap_use_adaptive_sampling = bpy.props.BoolProperty(
        name="Adaptive Sampling",
        default=True
    )
    bpy.types.Scene.vircadia_lightmap_adaptive_threshold = bpy.props.FloatProperty(
        name="Adaptive Threshold",
        default=0.01,
        min=0,
        max=1
    )
    bpy.types.Scene.vircadia_lightmap_samples = bpy.props.IntProperty(
        name="Samples",
        default=1024,
        min=1
    )
    bpy.types.Scene.vircadia_lightmap_adaptive_min_samples = bpy.props.IntProperty(
        name="Min Samples",
        default=0,
        min=0
    )
    bpy.types.Scene.vircadia_lightmap_use_denoising = bpy.props.BoolProperty(
        name="Use Denoising",
        default=True
    )
    bpy.types.Scene.vircadia_lightmap_denoiser = bpy.props.EnumProperty(
        name="Denoiser",
        items=[
            ('OPTIX', 'OptiX', 'Use OptiX denoiser'),
            ('OPENIMAGEDENOISE', 'OpenImageDenoise', 'Use OpenImageDenoise denoiser')
        ],
        default='OPTIX'
    )
    bpy.types.Scene.vircadia_lightmap_denoising_input_passes = bpy.props.EnumProperty(
        name="Denoising Passes",
        items=[
            ('RGB_ALBEDO', 'Albedo', 'Use Albedo pass for denoising'),
            ('RGB_ALBEDO_NORMAL', 'Albedo and Normal', 'Use Albedo and Normal passes for denoising')
        ],
        default='RGB_ALBEDO'
    )
    bpy.types.Scene.vircadia_lightmap_denoising_prefilter = bpy.props.EnumProperty(
        name="Denoising Prefilter",
        items=[
            ('ACCURATE', 'Accurate', 'Use accurate prefilter'),
            ('FAST', 'Fast', 'Use fast prefilter'),
            ('NONE', 'None', 'No prefilter')
        ],
        default='ACCURATE'
    )
    bpy.types.Scene.vircadia_lightmap_denoising_quality = bpy.props.EnumProperty(
        name="Denoising Quality",
        items=[
            ('HIGH', 'High', 'High quality denoising'),
            ('BALANCED', 'Balanced', 'Balanced quality denoising'),
            ('FAST', 'Fast', 'Fast denoising')
        ],
        default='HIGH'
    )

    bpy.utils.register_class(VIRCADIA_PT_lightmap_panel)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_PT_lightmap_panel)

    del bpy.types.Scene.vircadia_lightmap_color_space
    del bpy.types.Scene.vircadia_lightmap_resolution_single
    del bpy.types.Scene.vircadia_lightmap_resolution_small
    del bpy.types.Scene.vircadia_lightmap_resolution_large
    del bpy.types.Scene.vircadia_lightmap_small_threshold
    del bpy.types.Scene.vircadia_lightmap_large_threshold

    # Unregister properties for bake settings
    del bpy.types.Scene.vircadia_lightmap_bake_type
    del bpy.types.Scene.vircadia_lightmap_use_pass_direct
    del bpy.types.Scene.vircadia_lightmap_use_pass_indirect
    del bpy.types.Scene.vircadia_lightmap_use_pass_color
    del bpy.types.Scene.vircadia_lightmap_use_clear
    del bpy.types.Scene.vircadia_lightmap_use_adaptive_sampling
    del bpy.types.Scene.vircadia_lightmap_adaptive_threshold
    del bpy.types.Scene.vircadia_lightmap_samples
    del bpy.types.Scene.vircadia_lightmap_adaptive_min_samples
    del bpy.types.Scene.vircadia_lightmap_use_denoising
    del bpy.types.Scene.vircadia_lightmap_denoiser
    del bpy.types.Scene.vircadia_lightmap_denoising_input_passes
    del bpy.types.Scene.vircadia_lightmap_denoising_prefilter
    del bpy.types.Scene.vircadia_lightmap_denoising_quality

if __name__ == "__main__":
    register()