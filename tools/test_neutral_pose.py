import bpy
import math
import mathutils
import sys

# Args passed after '--'
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

la_x, la_y, la_z = float(args[0]), float(args[1]), float(args[2])
lf_x, lf_y, lf_z = float(args[3]), float(args[4]), float(args[5])
lh_x, lh_y, lh_z = float(args[6]), float(args[7]), float(args[8])
# Symmetrize manually or run for right arm
ra_x, ra_y, ra_z = float(args[9]), float(args[10]), float(args[11])
rf_x, rf_y, rf_z = float(args[12]), float(args[13]), float(args[14])
rh_x, rh_y, rh_z = float(args[15]), float(args[16]), float(args[17])


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v3.glb")

arm = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm = obj
        break

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

for pb in arm.pose.bones:
    pb.matrix_basis = mathutils.Matrix.Identity(4)

def set_euler(bone_name, rot):
    for pb in arm.pose.bones:
        if bone_name in pb.name or pb.name in bone_name:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2]))
            return

set_euler('LeftArm', (la_x, la_y, la_z))
set_euler('LeftForeArm', (lf_x, lf_y, lf_z))
set_euler('LeftHand', (lh_x, lh_y, lh_z))

set_euler('RightArm', (ra_x, ra_y, ra_z))
set_euler('RightForeArm', (rf_x, rf_y, rf_z))
set_euler('RightHand', (rh_x, rh_y, rh_z))

# Relax the fingers
fingers = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
for f in fingers:
    for i in range(1, 4):
        curl = -10 if i == 1 else -15
        if f == 'Thumb': curl = 5 
        # Apply generic curl
        set_euler(f"LeftHand{f}{i}", (curl, 0, 0))
        set_euler(f"RightHand{f}{i}", (curl, 0, 0))

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# Setup Render
camera_data = bpy.data.cameras.new(name='Camera')
camera_object = bpy.data.objects.new('Camera', camera_data)
bpy.context.collection.objects.link(camera_object)
bpy.context.scene.camera = camera_object
camera_data.lens = 50

light_data = bpy.data.lights.new(name='Light', type='SUN')
light_data.energy = 5
light_obj = bpy.data.objects.new(name='Light', object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (0, -2, 3)

bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.render.resolution_x = 512
bpy.context.scene.render.resolution_y = 512
bpy.context.scene.cycles.samples = 16
bpy.context.scene.render.image_settings.file_format = 'PNG'

# Render Front
camera_object.location = (0, -2.2, 1.0) 
camera_object.rotation_euler = (math.radians(85), 0, 0)
bpy.context.scene.render.filepath = r"C:\Users\PC\.gemini\antigravity\brain\ad0cf972-41cc-42d5-893d-2b8831a21d55\test_front.png"
bpy.ops.render.render(write_still=True)

# Render Side
camera_object.location = (2.2, 0, 1.0) 
camera_object.rotation_euler = (math.radians(85), 0, math.radians(90))
bpy.context.scene.render.filepath = r"C:\Users\PC\.gemini\antigravity\brain\ad0cf972-41cc-42d5-893d-2b8831a21d55\test_side.png"
bpy.ops.render.render(write_still=True)

# Also save an output file so we can inspect it using AvatarDiagnostic component if we want
neutral_action = bpy.data.actions.new(name="ASL_NEUTRAL")
if not arm.animation_data:
    arm.animation_data_create()
arm.animation_data.action = neutral_action
bpy.ops.object.mode_set(mode='POSE')
for pb in arm.pose.bones:
    pb.keyframe_insert(data_path="rotation_euler", frame=0)

export_path = r"d:\Singvox\Singvox\web\public\avatar\test_tuning.glb"
bpy.ops.export_scene.gltf(
    filepath=export_path,
    export_format='GLB',
    use_selection=False,
    export_animations=True,
    export_current_frame=True,
    export_animation_mode='ACTIONS',
)
print("COMPLETED RENDER TUNING")
