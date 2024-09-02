import bpy
from bpy.types import Panel
from bpy.props import EnumProperty

# Define allowed types
ALLOWED_ENTITY_TYPES = [
    'model',
    'shape',
    'light',
    'text',
    'web',
    'zone',
    'image',
]

ALLOWED_SHAPE_TYPES = [
    'box',
    'sphere',
    'isosahedron',
    'hexagon',
    'octagon',
    'cylinder',
    'cone',
    'circle',
    'quad',
]

BLENDER_PRIMITIVES = [
    ('PLANE', 'Plane', ''),
    ('CUBE', 'Cube', ''),
    ('CIRCLE', 'Circle', ''),
    ('UVSPHERE', 'UV Sphere', ''),
    ('ICOSPHERE', 'Ico Sphere', ''),
    ('CYLINDER', 'Cylinder', ''),
    ('CONE', 'Cone', ''),
    ('TORUS', 'Torus', ''),
    ('MONKEY', 'Monkey', ''),
]

class VIRCADIA_PT_entity_creation(Panel):
    bl_label = "Create Vircadia Entity"
    bl_idname = "VIEW3D_PT_vircadia_entity_creation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vircadia"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, "vircadia_entity_type")

        if scene.vircadia_entity_type == 'shape':
            layout.prop(scene, "vircadia_shape_type")
        elif scene.vircadia_entity_type == 'model':
            layout.prop(scene, "vircadia_primitive_type")

        layout.operator("vircadia.create_entity")

def get_entity_types(self, context):
    return [(t, t.capitalize(), "", i) for i, t in enumerate(ALLOWED_ENTITY_TYPES)]

def get_shape_types(self, context):
    return [(t, t.capitalize(), "", i) for i, t in enumerate(ALLOWED_SHAPE_TYPES)]

def register():
    bpy.types.Scene.vircadia_entity_type = EnumProperty(
        name="Entity Type",
        items=get_entity_types,
        default=1  # Index of 'shape' in ALLOWED_ENTITY_TYPES
    )

    bpy.types.Scene.vircadia_shape_type = EnumProperty(
        name="Shape Type",
        items=get_shape_types,
        default=0  # Index of 'box' in ALLOWED_SHAPE_TYPES
    )

    bpy.types.Scene.vircadia_primitive_type = EnumProperty(
        name="Primitive Type",
        items=BLENDER_PRIMITIVES,
        default='CUBE'
    )

    bpy.utils.register_class(VIRCADIA_PT_entity_creation)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_PT_entity_creation)

    del bpy.types.Scene.vircadia_primitive_type
    del bpy.types.Scene.vircadia_shape_type
    del bpy.types.Scene.vircadia_entity_type

if __name__ == "__main__":
    register()