import bpy
import json
import os
import uuid
from urllib.parse import urljoin
from .. import config
from ..utils import coordinate_utils, property_utils, visibility_utils

class VircadiaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            return f"{obj:.16f}"
        return super().default(obj)

def generate_random_uuid():
    return str(uuid.uuid4())

def replace_placeholder_uuid(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and value == "{10000000-0000-0000-0000-000000000000}":
                new_uuid = generate_random_uuid()
                data[key] = "{" + new_uuid + "}"
            elif isinstance(value, (dict, list)):
                replace_placeholder_uuid(value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, str) and item == "{10000000-0000-0000-0000-000000000000}":
                new_uuid = generate_random_uuid()
                data[i] = "{" + new_uuid + "}"
            elif isinstance(item, (dict, list)):
                replace_placeholder_uuid(item)

def update_template_properties(template, custom_props):
    for key, value in template.items():
        if isinstance(value, dict):
            update_template_properties(value, custom_props)
        else:
            prop_key = f"{key}"
            if prop_key in custom_props:
                if "Mode" in prop_key and prop_key.lower() != "model":
                    template[key] = "enabled" if custom_props[prop_key] else "disabled"
                else:
                    template[key] = custom_props[prop_key]
            else:
                for custom_key in custom_props:
                    if custom_key.endswith(f"_{key}"):
                        if "Mode" in custom_key and custom_key.lower() != "model":
                            template[key] = "enabled" if custom_props[custom_key] else "disabled"
                        else:
                            template[key] = custom_props[custom_key]
                        break

def get_vircadia_entity_data(obj, content_path):
    entity_type = obj.get("type", "Entity")
    
    # Load the appropriate template
    template = load_entity_template(entity_type.lower())
    entity_data = template["Entities"][0]

    # Update basic properties
    entity_data["id"] = "{" + generate_random_uuid() + "}"
    entity_data["type"] = entity_type
    entity_data["name"] = obj.get("name", "")

    # Convert coordinates for Zone and Web entities
    if entity_type.lower() in ["zone", "web"]:
        entity_data["position"] = coordinate_utils.blender_to_vircadia_coordinates(*obj.location)
        entity_data["rotation"] = coordinate_utils.blender_to_vircadia_rotation(*obj.rotation_quaternion)
        
        # Special handling for Web entity dimensions
        if entity_type.lower() == "web":
            entity_data["dimensions"] = {
                "x": obj.dimensions.x,
                "y": obj.dimensions.y,
                "z": 0.01  # Fixed Z dimension for web panels
            }
        else:
            entity_data["dimensions"] = coordinate_utils.blender_to_vircadia_dimensions(*obj.dimensions)
    elif entity_type.lower() == "model":
        entity_data["position"] = {
            "x": obj.location.x,
            "y": obj.location.y,
            "z": obj.location.z
        }
        entity_data["dimensions"] = {
            "x": obj.scale.x,
            "y": obj.scale.y,
            "z": obj.scale.z
        }
        entity_data["rotation"] = {
            "x": obj.rotation_quaternion.x,
            "y": obj.rotation_quaternion.y,
            "z": obj.rotation_quaternion.z,
            "w": obj.rotation_quaternion.w
        }
    else:
        entity_data["position"] = {
            "x": obj.location.x,
            "y": obj.location.y,
            "z": obj.location.z
        }
        entity_data["dimensions"] = {
            "x": obj.dimensions.x,
            "y": obj.dimensions.y,
            "z": obj.dimensions.z
        }
        entity_data["rotation"] = {
            "x": obj.rotation_quaternion.x,
            "y": obj.rotation_quaternion.y,
            "z": obj.rotation_quaternion.z,
            "w": obj.rotation_quaternion.w
        }

    # Get all custom properties
    custom_props = property_utils.get_custom_properties(obj)

    # Update template properties with custom properties
    update_template_properties(entity_data, custom_props)

    # Special handling for zone entities
    if entity_type.lower() == "zone":
        # Get the skybox URL from the scene properties
        skybox_url = bpy.context.scene.vircadia_skybox_texture
        if skybox_url:
            # Ensure the skybox property exists in entity_data
            if "skybox" not in entity_data:
                entity_data["skybox"] = {}
            entity_data["skybox"]["url"] = urljoin(content_path, os.path.basename(skybox_url))

        # Handle userData and renderingPipeline properties
        user_data = {}
        rendering_pipeline = {}

        for key, value in custom_props.items():
            if key.startswith("renderingPipeline_"):
                rendering_pipeline[key.replace("renderingPipeline_", "")] = value
            elif key == "environment_environmentTexture":
                if "environment" not in user_data:
                    user_data["environment"] = {}
                user_data["environment"]["environmentTexture"] = urljoin(content_path, os.path.basename(value))

        if rendering_pipeline:
            user_data["renderingPipeline"] = rendering_pipeline

        if user_data:
            entity_data["userData"] = json.dumps(user_data)

    return entity_data

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

def has_model_entities():
    collision_keywords = ["collider", "collision", "collides", "colliders", "collisions"]
    
    def is_collision_object(obj):
        return any(keyword in obj.name.lower() for keyword in collision_keywords)
    
    def is_excluded_entity(obj):
        excluded_types = ["zone", "web", "light", "image", "text", "shape"]  # Add more types here as needed
        return obj.get("type", "").lower() in excluded_types
    
    return any(
        obj.type == 'MESH' and
        not is_excluded_entity(obj) and
        not is_collision_object(obj)
        for obj in bpy.data.objects
    )

def has_collision_objects():
    collision_keywords = ["collider", "collision", "collides", "colliders", "collisions"]
    return any(any(keyword in obj.name.lower() for keyword in collision_keywords) for obj in bpy.data.objects)

def export_vircadia_json(context, filepath):
    scene = context.scene
    content_path = scene.vircadia_content_path

    if not content_path:
        raise ValueError("Content Path is not set. Please set it in the Vircadia panel before exporting.")

    if not content_path.endswith('/'):
        content_path += '/'

    scene_data = {
        "DataVersion": 0,
        "Entities": [],
        "Id": "{" + generate_random_uuid() + "}",
        "Version": 133
    }

    hidden_objects = visibility_utils.temporarily_unhide_objects(context)

    try:
        for obj in bpy.data.objects:
            if "type" in obj:
                entity_type = obj["type"].lower()
                if entity_type not in ["light", "model"]:
                    entity_data = get_vircadia_entity_data(obj, content_path)
                    scene_data["Entities"].append(entity_data)

        # Check if there are any Model entities in the Blender scene
        if has_model_entities():
            # Add the Model entity from the template
            model_template = load_entity_template("model")
            model_entity = model_template["Entities"][0]
            replace_placeholder_uuid(model_entity)
            model_entity["modelURL"] = urljoin(content_path, config.DEFAULT_GLB_EXPORT_FILENAME)
            scene_data["Entities"].append(model_entity)

        # Check if we need to add a collision model
        if has_collision_objects():
            collision_model_template = load_entity_template("model")
            collision_model_entity = collision_model_template["Entities"][0]
            replace_placeholder_uuid(collision_model_entity)
            collision_model_entity["modelURL"] = urljoin(content_path, config.DEFAULT_GLB_EXPORT_FILENAME.replace('.glb', '_collisions.glb'))
            collision_model_entity["collisionless"] = False
            collision_model_entity["ignoreForCollisions"] = False
            collision_model_entity["visible"] = False
            scene_data["Entities"].append(collision_model_entity)

        replace_placeholder_uuid(scene_data)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'w') as f:
            json.dump(scene_data, f, cls=VircadiaJSONEncoder, indent=4)

        print(f"Vircadia JSON exported successfully to {filepath}")
    finally:
        visibility_utils.restore_hidden_objects(hidden_objects)

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
    bpy.utils.unregister_class(EXPORT_OT_vircadia_json)