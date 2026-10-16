import bpy
import math
import mathutils
import os

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v3.glb")

arm = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm = obj
        break

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

# Clear all current pose transforms
for pb in arm.pose.bones:
    pb.matrix_basis = mathutils.Matrix.Identity(4)

# Create a new action for ASL_NEUTRAL
neutral_action = bpy.data.actions.new(name="ASL_NEUTRAL")
if not arm.animation_data:
    arm.animation_data_create()
arm.animation_data.action = neutral_action

def set_rot(bone_name, rot):
    if bone_name in arm.pose.bones:
        pb = arm.pose.bones[bone_name]
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = rot
        pb.keyframe_insert(data_path="rotation_euler", frame=0)

# To make the character relaxed:
# Mixamo's A-pose has arms spread horizontally slightly (~45 degrees) and somewhat forward.
# LeftArm drops down. RightArm drops down.
# Let's use simple rotations to drop the arms.
set_rot('mixamorig4:LeftArm', (0, 0, -math.radians(35)))
set_rot('mixamorig4:RightArm', (0, 0, math.radians(35)))

# Relax the elbows slightly so they aren't locked straight
set_rot('mixamorig4:LeftForeArm', (math.radians(10), 0, 0))
set_rot('mixamorig4:RightForeArm', (math.radians(10), 0, 0))

# Palms facing inwards (thumbs forward). We need to twist the forearm to face the palm inward.
# In mixamo, palm down/in usually involves twisting along Y. Let's try 45 degrees.
set_rot('mixamorig4:LeftForeArm', (math.radians(5), math.radians(45), 0))
set_rot('mixamorig4:RightForeArm', (math.radians(5), -math.radians(45), 0))

# Relax the hands slightly
set_rot('mixamorig4:LeftHand', (math.radians(-5), 0, math.radians(-10)))
set_rot('mixamorig4:RightHand', (math.radians(-5), 0, math.radians(10)))

# Curl fingers naturally 
fingers = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
for f in fingers:
    for i in range(1, 4):
        # Base phalanges bend ~15 deg, middle bend ~20 deg
        curl = math.radians(-15) if i == 1 else math.radians(-20)
        if f == 'Thumb': curl = math.radians(10) # Thumb is evaluated differently
        
        # Applying curl generically on X axis (flexion in Mixamo local bone space typically)
        lname = f"mixamorig4:LeftHand{f}{i}"
        rname = f"mixamorig4:RightHand{f}{i}"
        set_rot(lname, (curl, 0, 0))
        set_rot(rname, (curl, 0, 0))


bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# Render Setup
camera_data = bpy.data.cameras.new(name='Camera')
camera_object = bpy.data.objects.new('Camera', camera_data)
bpy.context.collection.objects.link(camera_object)
bpy.context.scene.camera = camera_object

light_data = bpy.data.lights.new(name='Light', type='SUN')
light_data.energy = 5
light_obj = bpy.data.objects.new(name='Light', object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (0, -2, 3)

bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800
bpy.context.scene.render.image_settings.file_format = 'PNG'

# Render Front
camera_object.location = (0, -2.5, 1.0) 
camera_object.rotation_euler = (math.radians(85), 0, 0)
bpy.context.scene.render.filepath = r"C:\Users\PC\.gemini\antigravity\brain\ad0cf972-41cc-42d5-893d-2b8831a21d55\neutral_front.png"
bpy.ops.render.render(write_still=True)

# Render Side
camera_object.location = (2.5, 0, 1.0) 
camera_object.rotation_euler = (math.radians(85), 0, math.radians(90))
bpy.context.scene.render.filepath = r"C:\Users\PC\.gemini\antigravity\brain\ad0cf972-41cc-42d5-893d-2b8831a21d55\neutral_side.png"
bpy.ops.render.render(write_still=True)

# Render 3/4
camera_object.location = (1.8, -1.8, 1.0) 
camera_object.rotation_euler = (math.radians(85), 0, math.radians(45))
bpy.context.scene.render.filepath = r"C:\Users\PC\.gemini\antigravity\brain\ad0cf972-41cc-42d5-893d-2b8831a21d55\neutral_3q.png"
bpy.ops.render.render(write_still=True)

print("Visuals rendered successfully")

# Export GLB securely protecting explicit ASL_HELLO Action outputs alongside ASL_NEUTRAL explicitly
export_path = r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v4_Neutral.glb"
bpy.ops.export_scene.gltf(
    filepath=export_path,
    export_format='GLB',
    use_selection=False,
    export_materials='EXPORT',
    export_animations=True,
    export_current_frame=True,
    export_animation_mode='ACTIONS', # Preserves ASL_HELLO natively alongside ASL_NEUTRAL implicitly!
    export_yup=True
)

print(f"Exported to {export_path}")
