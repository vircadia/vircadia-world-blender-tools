import math
from mathutils import Vector, Quaternion, Matrix

def vircadia_to_blender_coordinates(x, y, z):
    # Convert from Vircadia Y-up to Blender Z-up
    return x, -z, y

def blender_to_vircadia_coordinates(x, y, z):
    # Convert from Blender Z-up to Vircadia Y-up
    return x, z, -y
    
def vircadia_to_blender_dimensions(x, y, z):
    # Convert dimensions from Y-up to Z-up
    return x, z, y

def blender_to_vircadia_dimensions(x, y, z):
    # Convert dimensions from Z-up to Y-up
    return x, z, y

def vircadia_to_blender_rotation(x, y, z, w):
    # Create the Vircadia quaternion
    vircadia_quat = Quaternion((w, x, y, z))

    # Define a 90-degree rotation around the X-axis to convert from Y-up to Z-up
    rotation_quat = Quaternion((math.cos(math.pi / 4), math.sin(math.pi / 4), 0, 0))  # 90-degree rotation around X

    # Apply the 90-degree rotation to the Vircadia quaternion
    blender_quat = rotation_quat @ vircadia_quat

    # Return the result as a Blender quaternion (x, y, z, w)
    return (blender_quat.x, blender_quat.y, blender_quat.z, blender_quat.w)

def blender_to_vircadia_rotation(w, x, y, z):
    # Create the Blender quaternion
    blender_quat = Quaternion((w, x, y, z))

    # Define a -90-degree rotation around the X-axis to convert from Z-up to Y-up
    rotation_quat = Quaternion((math.cos(-math.pi / 4), math.sin(-math.pi / 4), 0, 0))  # -90-degree rotation around X

    # Apply the -90-degree rotation to the Blender quaternion
    vircadia_quat = rotation_quat @ blender_quat

    # Return the result as a Vircadia quaternion (x, y, z, w)
    return (vircadia_quat.x, vircadia_quat.y, vircadia_quat.z, vircadia_quat.w)


def euler_to_quaternion(roll, pitch, yaw):
    # Convert Euler angles to quaternion
    qx = math.sin(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) - math.cos(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    qy = math.cos(roll/2) * math.sin(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.cos(pitch/2) * math.sin(yaw/2)
    qz = math.cos(roll/2) * math.cos(pitch/2) * math.sin(yaw/2) - math.sin(roll/2) * math.sin(pitch/2) * math.cos(yaw/2)
    qw = math.cos(roll/2) * math.cos(pitch/2) * math.cos(yaw/2) + math.sin(roll/2) * math.sin(pitch/2) * math.sin(yaw/2)
    return qx, qy, qz, qw

def quaternion_to_euler(x, y, z, w):
    # Convert quaternion to Euler angles
    t0 = 2.0 * (w * x + y * z)
    t1 = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(t0, t1)

    t2 = 2.0 * (w * y - z * x)
    t2 = 1.0 if t2 > 1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch = math.asin(t2)

    t3 = 2.0 * (w * z + x * y)
    t4 = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(t3, t4)

    return roll, pitch, yaw
