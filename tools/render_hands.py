import bpy
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v6_Neutral.glb")

# Setup Render
camera_data = bpy.data.cameras.new(name='Camera')
camera_object = bpy.data.objects.new('Camera', camera_data)
bpy.context.collection.objects.link(camera_object)
bpy.context.scene.camera = camera_object
camera_data.lens = 80 # Zoom

light_data = bpy.data.lights.new(name='Light', type='SUN')
light_data.energy = 5
light_obj = bpy.data.objects.new(name='Light', object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (0, -2, 3)

bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.render.resolution_x = 400
bpy.context.scene.render.resolution_y = 300
bpy.context.scene.cycles.samples = 16
bpy.context.scene.render.image_settings.file_format = 'PNG'

# Render Hand Detail (Zoomed on Left Hand roughly around hip)
camera_object.location = (0.25, -0.6, 0.85) 
camera_object.rotation_euler = (math.radians(90), 0, 0)
bpy.context.scene.render.filepath = r"C:\Users\PC\.gemini\antigravity\brain\ad0cf972-41cc-42d5-893d-2b8831a21d55\test_hand.png"
bpy.ops.render.render(write_still=True)
print("COMPLETED HAND RENDER")
