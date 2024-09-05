import bpy
import json
import os
from urllib.parse import urljoin
from .. import config
from ..utils import coordinate_utils, property_utils

def get_vircadia_entity_data(obj, content_path):
    entity_data = {}

    entity_type = obj.get("type", "Entity")
    entity_data["type"] = entity_type

    blender_pos = obj.location
    vircadia_pos = coordinate_utils.blender_to_vircadia_coordinates(*blender_pos)
    entity_data["position"] = {"x": vircadia_pos[0], "y": vircadia_pos[1], "z": vircadia_pos[2]}

    blender_scale = obj.scale
    vircadia_scale = coordinate_utils.blender_to_vircadia_coordinates(*blender_scale)
    entity_data["dimensions"] = {"x": vircadia_scale[0], "y": vircadia_scale[1], "z": vircadia_scale[2]}

    if obj.rotation_mode == 'QUATERNION':
        blender_rot = obj.rotation_quaternion
    else:
        blender_rot = obj.rotation_euler.to_quaternion()
    vircadia_rot = coordinate_utils.blender_to_vircadia_rotation(*blender_rot)
    entity_data["rotation"] = {"x": vircadia_rot[0], "y": vircadia_rot[1], "z": vircadia_rot[2], "w": vircadia_rot[3]}

    custom_props = property_utils.get_custom_properties(obj)
    entity_data.update(reconstruct_entity_properties(custom_props, entity_type))

    if entity_type.lower() == "zone":
        entity_data["userData"] = construct_zone_user_data(obj)

    return entity_data

def reconstruct_entity_properties(props, entity_type):
    reconstructed = {}
    for key, value in props.items():
        if key in ["position", "dimensions", "rotation", "type"]:
            continue  # These are handled separately

        parts = key.split('_')
        current = reconstructed
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        final_key = parts[-1]
        if final_key in ['red', 'green', 'blue']:
            if 'color' not in current:
                current['color'] = {}
            current['color'][final_key] = value
        elif final_key in ['x', 'y', 'z', 'w']:
            if 'direction' not in current:
                current['direction'] = {}
            current['direction'][final_key] = value
        elif final_key.lower().endswith('mode') and final_key.lower() != 'model':
            current[final_key] = "enabled" if value else "disabled"
        else:
            current[final_key] = value

    # Handle specific entity type structures
    if entity_type.lower() == "zone":
        for mode in ["keyLightMode", "ambientLightMode", "skyboxMode", "hazeMode", "bloomMode"]:
            if mode not in reconstructed:
                reconstructed[mode] = "enabled" if reconstructed.get(mode.replace("Mode", "")) else "disabled"

    return reconstructed

def construct_zone_user_data(obj):
    user_data = {
        "renderingPipeline": {
            "fxaaEnabled": obj.get("renderingPipeline_fxaaEnabled", True),
            "glowLayerEnabled": obj.get("renderingPipeline_glowLayerEnabled", True),
            "glowLayer": {
                "blurKernelSize": obj.get("renderingPipeline_glowLayer_blurKernelSize", 16),
                "intensity": obj.get("renderingPipeline_glowLayer_intensity", 1.5)
            }
        },
        "environment": {
            "environmentTexture": obj.get("environment_environmentTexture", "")
        }
    }
    return json.dumps(user_data)

def load_entity_template(entity_type):
    addon_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    
    # Map entity types to their corresponding template files
    template_map = {
        "box": "shape",
        "sphere": "shape",
        "shape": "shape",
        # Add other shape types here as needed
    }
    
    # Get the correct template name, defaulting to the entity type if not in the map
    template_name = template_map.get(entity_type.lower(), entity_type.lower())
    
    template_path = os.path.join(addon_path, "templates", f"template_{template_name}.json")
    
    try:
        with open(template_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Template file not found for entity type '{entity_type}'. Using generic entity template.")
        # Provide a basic generic template as fallback
        return {"Entities": [{"type": entity_type}]}

def export_vircadia_json(context, filepath):
    scene = context.scene
    content_path = scene.vircadia_content_path

    if not content_path:
        raise ValueError("Content Path is not set. Please set it in the Vircadia panel before exporting.")

    if not content_path.endswith('/'):
        content_path += '/'

    scene_data = {"Entities": []}

    # Add the Model entity from the template
    model_template = load_entity_template("model")
    model_entity = model_template["Entities"][0]
    model_entity["modelURL"] = urljoin(content_path, config.DEFAULT_GLB_EXPORT_FILENAME)
    scene_data["Entities"].append(model_entity)

    for obj in bpy.data.objects:
        if "type" in obj:
            entity_type = obj["type"].lower()
            if entity_type not in ["light", "model"]:
                entity_data = get_vircadia_entity_data(obj, content_path)
                
                # Merge with template
                template = load_entity_template(entity_type)
                template_entity = template["Entities"][0]
                merged_entity = {**template_entity, **entity_data}
                
                scene_data["Entities"].append(merged_entity)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w') as f:
        json.dump(scene_data, f, indent=2)

    print(f"Vircadia JSON exported successfully to {filepath}")

class EXPORT_OT_vircadia_json(bpy.types.Operator):
    bl_idname = "export_scene.vircadia_json"
    bl_label = "Export Vircadia JSON"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if not blend_filepath:
                blend_filepath = "untitled"
            else:
                blend_filepath = os.path.splitext(blend_filepath)[0]
            self.filepath = os.path.join(os.path.dirname(blend_filepath), config.DEFAULT_JSON_EXPORT_FILENAME)

        export_vircadia_json(context, self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = config.DEFAULT_JSON_EXPORT_FILENAME
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def register():
    bpy.utils.register_class(EXPORT_OT_vircadia_json)

def unregister():
    try:
        bpy.utils.unregister_class(EXPORT_OT_vircadia_json)
    except RuntimeError:
        print(f"Warning: {EXPORT_OT_vircadia_json.__name__} was not registered, skipping unregister.")