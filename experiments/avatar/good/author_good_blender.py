"""Author candidate ASL_GOOD on a COPY of the avatar — never the production GLB.

Mirrors Singvox/tools/author_hello.py conventions:
- Blender bone names 'mixamorig4:<Bone>' in POSE mode, XYZ euler, keyframe_insert rotation_euler.
- Neutral in/out so AvatarController 'finished' -> ASL_NEUTRAL crossfade stays clean.
- Flat/open right hand: fingers straight (do NOT feed 366-dim recognition vectors into joints).

Usage (user machine with Blender + avatar .blend):
    blender --background --python Singvox/experiments/avatar/good/author_good_blender.py
Then export a COPY (see tools/export_glb.py) and test playSignByLabel('GOOD') in AvatarStudio.
"""
import bpy
import math  # noqa: F401  (kept for parity with author_hello.py tuning)

SOURCE_BLEND = r"d:\Singvox\Singvox\avatar\exports\SignVox_HELLO_BlendRepair.blend"
SAVE_BLEND = r"d:\Singvox\Singvox\experiments\avatar\good\SignVox_GOOD_Candidate.blend"
CLIP_NAME = "ASL_GOOD"

bpy.ops.wm.read_homefile(filepath=SOURCE_BLEND)

arm = bpy.data.objects.get("Armature") or bpy.data.objects.get("Armature.001")
bpy.context.view_layer.objects.active = arm
arm.hide_viewport = False
arm.hide_set(False)

bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.transforms_clear()

old = bpy.data.actions.get(CLIP_NAME)
if old:
    bpy.data.actions.remove(old)

new_act = bpy.data.actions.new(CLIP_NAME)
if not arm.animation_data:
    arm.animation_data_create()
arm.animation_data.action = new_act


def set_rot(bone_name, euler_xyz, frame):
    bone = arm.pose.bones.get(f"mixamorig4:{bone_name}")
    if bone:
        bone.rotation_mode = 'XYZ'
        bone.rotation_euler = euler_xyz
        bone.keyframe_insert(data_path="rotation_euler", frame=frame)


def set_finger(side, finger, curl_euler_x, frame):
    """Straighten (0.0) or curl (>0) finger joints; flat hand => ~0.0."""
    for i in (1, 2, 3):
        bone = arm.pose.bones.get(f"mixamorig4:{side}Hand{finger}{i}")
        if bone:
            bone.rotation_mode = 'XYZ'
            bone.rotation_euler = (curl_euler_x, 0, 0)
            bone.keyframe_insert(data_path="rotation_euler", frame=frame)


# ---- Frame 0: Neutral (arms down, matches author_hello.py) ----
set_rot("LeftArm", (0, 0, -1.2), 0)
set_rot("RightArm", (0, 0, 1.2), 0)
set_rot("LeftForeArm", (0, 0, 0), 0)
set_rot("RightForeArm", (0, 0, 0), 0)
set_rot("LeftHand", (0, 0, 0), 0)
set_rot("RightHand", (0, 0, 0), 0)

# ---- Frame 10: Onset — flat right hand at lips/lower face (SV-ASL-002) ----
set_rot("LeftArm", (0, 0, -1.2), 10)
set_rot("RightArm", (0.55, 0.35, 0.55), 10)
set_rot("RightForeArm", (0, -0.5, 1.9), 10)
set_rot("RightHand", (0.4, -0.4, -0.4), 10)
for f in ("Index", "Middle", "Ring", "Pinky"):
    set_finger("Right", f, 0.0, 10)

# ---- Frame 20: Stroke — hand moves away/down-forward, opening outward ----
set_rot("LeftArm", (0, 0, -1.2), 20)
set_rot("RightArm", (0.9, 0.1, 0.45), 20)
set_rot("RightForeArm", (0, -0.1, 0.7), 20)
set_rot("RightHand", (0.1, -0.15, -0.15), 20)
for f in ("Index", "Middle", "Ring", "Pinky"):
    set_finger("Right", f, 0.0, 20)

# ---- Frame 40: Return neutral ----
set_rot("LeftArm", (0, 0, -1.2), 40)
set_rot("RightArm", (0, 0, 1.2), 40)
set_rot("LeftForeArm", (0, 0, 0), 40)
set_rot("RightForeArm", (0, 0, 0), 40)
set_rot("LeftHand", (0, 0, 0), 40)
set_rot("RightHand", (0, 0, 0), 40)
for f in ("Index", "Middle", "Ring", "Pinky"):
    set_finger("Right", f, 0.0, 40)

bpy.ops.wm.save_as_mainfile(filepath=SAVE_BLEND)
print(f"CANDIDATE {CLIP_NAME} BLOCKED OUT -> {SAVE_BLEND}")
