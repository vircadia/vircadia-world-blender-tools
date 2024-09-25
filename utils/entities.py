
ALL_ENTITY_TYPES = [
    "model",
    "shape",
    "light",
    "text",
    "web",
    "zone",
    "image",
]

ENTITY_TEMPLATES_JSON = {
    "model": "template_model.json",
    "shape": "template_shape.json",
    "light": "template_light.json",
    "text": "template_text.json",
    "web": "template_web.json",
    "zone": "template_zone.json",
    "image": "template_image.json",
}

def get_filtered_entity_types():
    # List of entity types to exclude
    excluded_types = ["particle", "image", "shape", "light"]  # Add any types you want to exclude here
    return [t for t in ALL_ENTITY_TYPES if t not in excluded_types]

# Use this function to get the filtered list of entity types
ENTITY_TYPES = get_filtered_entity_types()