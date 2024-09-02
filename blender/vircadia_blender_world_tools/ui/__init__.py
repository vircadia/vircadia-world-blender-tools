from . import custom_properties_panel
from . import entity_creation_panel

def register():
    custom_properties_panel.register()
    entity_creation_panel.register()

def unregister():
    entity_creation_panel.unregister()
    custom_properties_panel.unregister()