import json

def load_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except PermissionError:
        log_error(f"Permission denied when trying to read {file_path}")
    except FileNotFoundError:
        log_error(f"File not found: {file_path}")
    except json.JSONDecodeError:
        log_error(f"Invalid JSON file: {file_path}")
    return None

def log_error(message):
    print(f"Error: {message}")

def log_warning(message):
    print(f"Warning: {message}")

def log_import_error(entity):
    name = entity.get("name", "Unnamed")
    log_error(f"Failed to create object for entity: {name}")
