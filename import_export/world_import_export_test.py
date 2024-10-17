import unittest
import bpy
import bmesh
import tempfile
import os
import random
import time
from .world_export import GLTFExporter

class TestGLTFExporter(unittest.TestCase):
    @staticmethod
    def create_complex_mesh(name, vertices, faces):
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        
        bm = bmesh.new()
        for v in vertices:
            bm.verts.new(v)
        bm.verts.ensure_lookup_table()
        for f in faces:
            try:
                bm.faces.new([bm.verts[i] for i in f])
            except ValueError:
                # Skip faces with duplicate vertices
                continue
        
        bm.to_mesh(mesh)
        bm.free()
        
        return obj

    @staticmethod
    def create_complex_material(name):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Clear default nodes
        nodes.clear()
        
        # Create complex node setup
        output = nodes.new(type='ShaderNodeOutputMaterial')
        principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        texture = nodes.new(type='ShaderNodeTexNoise')
        mapping = nodes.new(type='ShaderNodeMapping')
        texcoord = nodes.new(type='ShaderNodeTexCoord')
        links.new(texcoord.outputs['UV'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], texture.inputs['Vector'])
        links.new(texture.outputs['Fac'], principled.inputs['Base Color'])
        links.new(principled.outputs['BSDF'], output.inputs['Surface'])
        return mat

    def create_complex_objects(self, num_objects=100):
        objects = []
        for i in range(num_objects):
            # Generate random complex mesh
            vertices = [(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)) for _ in range(50)]
            faces = []
            for _ in range(30):
                face = random.sample(range(50), 4)  # Ensure unique vertices for each face
                faces.append(face)
            obj = self.create_complex_mesh(f"ComplexObject_{i}", vertices, faces)
            
            # Add complex material
            mat = self.create_complex_material(f"ComplexMaterial_{i}")
            obj.data.materials.append(mat)
            
            # Set random location
            obj.location = (random.uniform(-10, 10), random.uniform(-10, 10), random.uniform(-10, 10))
            
            # Add object to the active collection and link to the scene
            bpy.context.collection.objects.link(obj)
            
            objects.append(obj)
        return objects

    def test_create_and_export_complex_objects(self):
        num_objects = 10
        timings = {}

        # Create complex objects
        start_time = time.time()
        objects = self.create_complex_objects(num_objects)
        timings['create_objects'] = time.time() - start_time

        # Export objects
        start_time = time.time()
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "complex_objects_export.glb")
            GLTFExporter.export_objects_to_gltf(objects, export_path)
        timings['export_objects'] = time.time() - start_time

        # Clean up: delete the objects
        start_time = time.time()
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects:
            obj.select_set(True)
        bpy.ops.object.delete()
        timings['cleanup'] = time.time() - start_time

        # Calculate total execution time
        total_time = sum(timings.values())
        fps = 1 / total_time if total_time > 0 else float('inf')

        # Print detailed timings
        print("\nDetailed Timings:")
        for step, duration in timings.items():
            print(f"{step}: {duration:.2f} seconds")
        print(f"\nTotal Execution time: {total_time:.2f} seconds")
        print(f"Equivalent FPS: {fps:.2f}")

        # Assertions
        self.assertGreater(total_time, 0, "Total execution time should be positive")
        self.assertGreater(fps, 0, "FPS should be positive")
        # You can add more specific assertions based on your performance requirements
        # For example:
        # self.assertGreater(fps, 30, "Export should be faster than 30 FPS")

if __name__ == "__main__":
    unittest.main()