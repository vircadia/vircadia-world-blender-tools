import bpy
from bpy.types import Panel

class VIRCADIA_PT_convert_to_vircadia(Panel):
    bl_label = "Convert to Vircadia"
    bl_idname = "VIEW3D_PT_vircadia_convert"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Vircadia"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None or obj.type != 'MESH':
            return False
        
        # Check if the object has any custom properties besides ant_landscape
        for prop in obj.keys():
            if not prop.startswith("ant_"):
                return False
        
        return True

    def draw(self, context):
        layout = self.layout
        layout.operator("vircadia.convert_to_vircadia")

def register():
    bpy.utils.register_class(VIRCADIA_PT_convert_to_vircadia)

def unregister():
    bpy.utils.unregister_class(VIRCADIA_PT_convert_to_vircadia)

if __name__ == "__main__":
    register()