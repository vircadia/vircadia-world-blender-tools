from . import export_operators
from . import import_operators
from . import entity_creation_operators
from . import convert_to_vircadia_operators
from . import clipboard_operators
from . import lightmap_operators

def register():
    export_operators.register()
    import_operators.register()
    entity_creation_operators.register()
    convert_to_vircadia_operators.register()
    clipboard_operators.register()
    lightmap_operators.register()

def unregister():
    lightmap_operators.unregister()
    clipboard_operators.unregister()
    convert_to_vircadia_operators.unregister()
    entity_creation_operators.unregister()
    import_operators.unregister()
    export_operators.unregister()