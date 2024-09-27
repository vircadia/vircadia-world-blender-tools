import math
from mathutils import Vector, Quaternion

def vircadia_to_blender_coordinates(x, y, z):
    # Convert from Y-up to Z-up
    return x, z, -y

def vircadia_to_blender_dimensions(x, y, z):
    # Convert dimensions from Y-up to Z-up
    return x, z, y

def blender_to_vircadia_coordinates(x, y, z):
    # Convert from Z-up to Y-up
    return x, -z, y

def blender_to_vircadia_dimensions(x, y, z):
    # Convert dimensions from Z-up to Y-up
    return x, z, y

def vircadia_to_blender_rotation(x, y, z, w):
    # Convert quaternion from Y-up to Z-up
    return Quaternion((w, x, -z, y))

def blender_to_vircadia_rotation(x, y, z, w):
    # Convert quaternion from Z-up to Y-up
    return x, -z, y, w

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

def vircadia_to_blender_scale(x, y, z):
    # Vircadia uses dimensions, Blender uses scale
    # Assuming a default cube size of 1x1x1 in Blender
    return x, z, y

def blender_to_vircadia_scale(x, y, z):
    # Blender uses scale, Vircadia uses dimensions
    # Assuming a default cube size of 1x1x1 in Blender
    return x, z, y