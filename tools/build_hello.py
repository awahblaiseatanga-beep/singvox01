import bpy
import mathutils
import math

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_Competition_Prototype.glb")

arm = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm = obj
        break

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

def set_euler(bone_name, rot):
    for pb in arm.pose.bones:
        if bone_name in pb.name or pb.name in bone_name:
            pb.rotation_mode = 'XYZ'
            pb.rotation_euler = (math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2]))
            return

def keyframe_all(frame):
    for pb in arm.pose.bones:
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)
        pb.keyframe_insert(data_path="location", frame=frame)

# Clean out old bad Actions
for action in bpy.data.actions:
    if "HELLO" in action.name:
        bpy.data.actions.remove(action)

hello_action = bpy.data.actions.new(name="ASL_HELLO")
if not arm.animation_data: arm.animation_data_create()
arm.animation_data.action = hello_action

# Right arm Neutral limits (mirrored from my optimal output):
ra_n = (10, 15, 0)
rf_n = (30, 120, -40)
rh_n = (85, -85, -80)

# Right arm Head limits (approximated salute)
ra_h = (80, 20, 20)      # Raise shoulder and point forward-ish
rf_h = (-100, 30, -30)   # Bend elbow 100 degrees
rh_h = (20, 20, -20)     # Align hand

# Frame 0: Neutral
set_euler('RightArm', ra_n)
set_euler('RightForeArm', rf_n)
set_euler('RightHand', rh_n)
# Left Arm stays neutral
set_euler('LeftArm', (10, -15, 0))
set_euler('LeftForeArm', (30, -120, 40))
set_euler('LeftHand', (85, 85, 80))
keyframe_all(0)

# Frame 15: Salute / Forehead touch
set_euler('RightArm', ra_h)
set_euler('RightForeArm', rf_h)
set_euler('RightHand', rh_h)
keyframe_all(15)

# Frame 25: Salute outward
set_euler('RightArm', (70, 40, -20))
set_euler('RightForeArm', (-40, 50, -40))
set_euler('RightHand', (0, 0, 0))
keyframe_all(25)

# Frame 40: Return to Neutral
set_euler('RightArm', ra_n)
set_euler('RightForeArm', rf_n)
set_euler('RightHand', rh_n)
keyframe_all(40)

# Export the Competition Prototype overriding the file
export_path = r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_Competition_Prototype.glb"
bpy.ops.export_scene.gltf(
    filepath=export_path,
    export_format='GLB',
    use_selection=False,
    export_animations=True,
    export_current_frame=True,
    export_animation_mode='ACTIONS',
)
print("HELLO GENERATED PROTOTYPE")

