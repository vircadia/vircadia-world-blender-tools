from . import main_panel
from . import custom_properties_panel
from . import entity_creation_panel
from . import convert_to_vircadia_panel
from . import lightmap_panel

def register():
    main_panel.register()
    custom_properties_panel.register()
    entity_creation_panel.register()
    convert_to_vircadia_panel.register()
    lightmap_panel.register()

def unregister():
    lightmap_panel.unregister()
    convert_to_vircadia_panel.unregister()
    entity_creation_panel.unregister()
    custom_properties_panel.unregister()
    main_panel.unregister()