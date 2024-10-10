from . import old_json_importer
from . import old_json_exporter
from . import gltf_importer
from . import old_gltf_exporter

def register():
    old_json_importer.register()
    old_json_exporter.register()
    gltf_importer.register()
    old_gltf_exporter.register()

def unregister():
    old_gltf_exporter.unregister()
    gltf_importer.unregister()
    old_json_exporter.unregister()
    old_json_importer.unregister()
