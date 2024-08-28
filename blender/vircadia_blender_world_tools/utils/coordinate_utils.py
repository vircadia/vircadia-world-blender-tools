def vircadia_to_blender_coordinates(x, y, z):
    # Convert from Y-up (right-handed) to Z-up (right-handed)
    return x, -z, y

def blender_to_vircadia_coordinates(x, y, z):
    # Convert from Z-up (right-handed) to Y-up (right-handed)
    return x, z, -y

def vircadia_to_blender_rotation(x, y, z, w):
    # Convert quaternion from Y-up to Z-up
    return w, x, -z, y

def blender_to_vircadia_rotation(w, x, y, z):
    # Convert quaternion from Z-up to Y-up
    return x, -z, y, w
