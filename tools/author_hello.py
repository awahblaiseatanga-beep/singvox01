import bpy
import math

bpy.ops.wm.read_homefile(filepath=r"d:\Singvox\Singvox\avatar\exports\SignVox_HELLO_BlendRepair.blend")

arm = bpy.data.objects.get("Armature")
bpy.context.view_layer.objects.active = arm
arm.hide_viewport = False
arm.hide_set(False)

bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.transforms_clear()

act = bpy.data.actions.get("ASL_HELLO")
if act:
    bpy.data.actions.remove(act)

new_act = bpy.data.actions.new("ASL_HELLO")
if not arm.animation_data:
    arm.animation_data_create()
arm.animation_data.action = new_act
arm.animation_data.nla_tracks.new().name = "ASL_HELLO"
arm.animation_data.nla_tracks["ASL_HELLO"].strips.new("HELLO", 0, new_act)

def set_rot(bone_name, euler_rot_xyz, frame):
    bone = arm.pose.bones.get(f"mixamorig4:{bone_name}")
    if bone:
        bone.rotation_mode = 'XYZ'
        bone.rotation_euler = euler_rot_xyz
        bone.keyframe_insert(data_path="rotation_euler", frame=frame)

# Frame 0: Neutral (Arms Down)
set_rot("LeftArm", (0, 0, -1.2), 0)
set_rot("RightArm", (0, 0, 1.2), 0)
set_rot("LeftForeArm", (0, 0, 0), 0)
set_rot("RightForeArm", (0, 0, 0), 0)
set_rot("LeftHand", (0, 0, 0), 0)
set_rot("RightHand", (0, 0, 0), 0)

# Frame 10: Salute start (Hand near forehead)
# Arm goes up and forward, forearm bends sharply, wrist twists palm down/forward
set_rot("LeftArm", (0, 0, -1.2), 10)
set_rot("RightArm", (0.5, 0.4, 0.6), 10) # Raise up and slightly forward
set_rot("RightForeArm", (0, -0.6, 2.0), 10) # Sharp bend
set_rot("RightHand", (0.5, -0.5, -0.5), 10) # Twist to match head

# Frame 20: Salute out (Hand flicks away forward)
set_rot("LeftArm", (0, 0, -1.2), 20)
set_rot("RightArm", (0.8, -0.2, 0.5), 20)
set_rot("RightForeArm", (0, 0, 0.8), 20)
set_rot("RightHand", (0, -0.2, -0.2), 20)

# Frame 30: Return Neutral
set_rot("LeftArm", (0, 0, -1.2), 30)
set_rot("RightArm", (0, 0, 1.2), 30)
set_rot("RightForeArm", (0, 0, 0), 30)
set_rot("RightHand", (0, 0, 0), 30)

bpy.ops.wm.save_as_mainfile(filepath=r"d:\Singvox\Singvox\avatar\exports\SignVox_HELLO_BlendRepair.blend")
print("MANUAL ASL_HELLO BLOCKED OUT")
