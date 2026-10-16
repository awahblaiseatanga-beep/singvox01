import bpy
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v3.glb")

arm = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm = obj
        break

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

pose_bone = arm.pose.bones["mixamorig4:LeftForeArm"]
pose_bone.rotation_mode = 'XYZ'

# Natively rotate forearm 90 degrees strictly along its local Twist Axis (Y)
# Mixamo bones natively track their length down Y locally.
pose_bone.rotation_euler = (0, math.pi / 2, 0)

# Shift shoulder down slightly to put it broadly across the chest for a good render
shoulder = arm.pose.bones["mixamorig4:LeftShoulder"]
shoulder.rotation_mode = 'XYZ'
shoulder.rotation_euler = (0.2, 0, 0)

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# Render Setup focusing specifically on the Left Arm/Chest
camera_data = bpy.data.cameras.new(name='Camera')
camera_object = bpy.data.objects.new('Camera', camera_data)
bpy.context.collection.objects.link(camera_object)
bpy.context.scene.camera = camera_object

# Position near left shoulder/chest tracking closely
camera_object.location = (0.5, -0.6, 1.4) 
camera_object.rotation_euler = (math.radians(80), 0, math.radians(45))

light_data = bpy.data.lights.new(name='Light', type='SUN')
light_data.energy = 5
light_obj = bpy.data.objects.new(name='Light', object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (0, -2, 3)

bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 600
bpy.context.scene.render.image_settings.file_format = 'PNG'
out_path = r"C:\Users\PC\.gemini\antigravity\brain\ad0cf972-41cc-42d5-893d-2b8831a21d55\twist_validation.png"
bpy.context.scene.render.filepath = out_path

bpy.ops.render.render(write_still=True)
print(f"Artifact rendered successfully to {out_path}")
