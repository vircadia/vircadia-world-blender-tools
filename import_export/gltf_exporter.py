import bpy
import os
import tempfile

class GLTFExporter:
    @staticmethod
    def export_collection_to_gltf(collection, export_path):
        # Select only the objects in our collection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collection.objects:
            obj.select_set(True)

        # Export
        bpy.ops.export_scene.gltf(
            filepath=export_path,
            use_selection=True,
            export_format='GLB',
            export_apply=True,
            export_vertex_color="MATERIAL",
            export_materials='EXPORT',
            export_normals=True,
            export_draco_mesh_compression_enable=True,
            export_draco_mesh_compression_level=6,
            export_animations=False,
            export_lights=False,
            export_cameras=False,
            export_extras=True,
            export_yup=True,
            export_copyright="Vircadia Complex Test Export"
        )

    @staticmethod
    def export_objects_to_gltf(objects, export_path):
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a temporary collection
            temp_collection = bpy.data.collections.new("TempExportCollection")
            bpy.context.scene.collection.children.link(temp_collection)

            # Link objects to the temporary collection
            for obj in objects:
                temp_collection.objects.link(obj)

            # Export the collection
            GLTFExporter.export_collection_to_gltf(temp_collection, export_path)

            # Clean up: remove the temporary collection
            bpy.data.collections.remove(temp_collection)