"""Author candidate ASL_GOOD by retargeting the avatar's own validated ASL_HELLO clip.

Why: hand-tuned XYZ eulers (v1) were expressed in the HELLO-.blend rest frame and,
on the production GLB bind pose, sent the right hand behind the back (verified
on-avatar 2026-10-15). This version (v2) derives GOOD from the shipped, visually
accepted ASL_HELLO motion: GOOD ~= small salute (lips instead of forehead).
Linguistically GOOD (flat hand to lips/chin, moving down-forward) is close to a
reduced salute, so slerping between HELLO's neutral and salute peak in Blender
pose space is principled — no guessed eulers, no landmark-to-joint mapping.

Usage (headless, paths after `--`):
    blender --background --python author_good_blender.py -- <source.glb|.blend> <out.blend>
Defaults: production GLB (read-only) -> scratch candidate .blend next to this script.
Saves ONLY the out path. Never touches production assets.
"""
import bpy
import os
import sys
from mathutils import Quaternion

_argv = sys.argv
_cli = _argv[_argv.index("--") + 1:] if "--" in _argv else []
_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else ""

SOURCE = _cli[0] if len(_cli) > 0 else \
    r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_Competition_Prototype.glb"
SAVE = _cli[1] if len(_cli) > 1 else os.path.join(_HERE, "SignVox_GOOD_Candidate.blend")
CLIP = "ASL_GOOD"

FPS = 30          # match ASL_GOOD.clip.json
F0, F_ONSET, F_STROKE, F_END = 0, 10, 20, 40
HELLO_T_NEUTRAL = 0.0   # s, HELLO clip start (rest-ish)
HELLO_T_PEAK = 0.5      # s, salute peak (verified in GLB: max elbow bend)
ONSET_BLEND = 0.78      # GOOD onset  = near-salute -> hand at lips/chin (below forehead)
STROKE_BLEND = 0.55     # GOOD stroke = hand forward-down of lips along the salute path

print(f"SOURCE: {SOURCE}\nSAVE:   {SAVE}")
if not os.path.exists(SOURCE):
    raise SystemExit(f"ERROR: source not found: {SOURCE}")

def _set_timing():
    # NOTE: must run AFTER read_factory_settings (which resets the scene).
    bpy.context.scene.render.fps = FPS
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = F_END

if SOURCE.lower().endswith(".glb"):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _set_timing()
    bpy.ops.import_scene.gltf(filepath=SOURCE)
else:
    try:
        bpy.ops.wm.open_mainfile(filepath=SOURCE)
    except Exception:
        bpy.ops.wm.read_homefile(filepath=SOURCE)
    _set_timing()

arm = next((o for o in bpy.context.scene.objects if o.type == 'ARMATURE'), None)
if not arm:
    raise SystemExit("ERROR: no armature found after source load")
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

hello = next((a for a in bpy.data.actions if 'ASL_HELLO' in a.name), None)
if not hello:
    raise SystemExit(f"ERROR: no ASL_HELLO action to retarget from. Actions: {[a.name for a in bpy.data.actions]}")
print(f"Retarget source action: {hello.name}")
mixamo = next((a for a in bpy.data.actions if 'mixamo' in a.name.lower()), None)
if not mixamo:
    raise SystemExit("ERROR: no mixamo neutral action for the resting left side")
print(f"Left-side neutral action: {mixamo.name}")

RIGHT = [b.name for b in arm.pose.bones if b.name.startswith('mixamorig4:Right')]
LEFT = [b.name for b in arm.pose.bones if b.name.startswith('mixamorig4:Left')]
print(f"Right-side bones: {len(RIGHT)}, left-side bones: {len(LEFT)}")

# Work in quaternion pose space.
for name in RIGHT + LEFT:
    arm.pose.bones[name].rotation_mode = 'QUATERNION'

if not arm.animation_data:
    arm.animation_data_create()
arm.animation_data.action = hello
scene = bpy.context.scene


def pose_at(action, t_sec, names):
    """Evaluate action at t_sec, return {bone: Quaternion} in pose space."""
    arm.animation_data.action = action
    scene.frame_set(round(t_sec * FPS))
    bpy.context.view_layer.update()
    return {name: arm.pose.bones[name].rotation_quaternion.copy() for name in names}


neutral = pose_at(hello, HELLO_T_NEUTRAL, RIGHT)
peak = pose_at(hello, HELLO_T_PEAK, RIGHT)
left_rest = pose_at(mixamo, 0.0, LEFT)
print(f"neutral RightArm: {neutral['mixamorig4:RightArm']}")
print(f"peak    RightArm: {peak['mixamorig4:RightArm']}")

old = bpy.data.actions.get(CLIP)
if old:
    bpy.data.actions.remove(old)
good = bpy.data.actions.new(CLIP)
arm.animation_data.action = good


def pose_bones(factors):
    """factors: {bone: slerp factor neutral->peak}. Writes keyframes at current frame."""
    for name in RIGHT:
        q = neutral[name].slerp(peak[name], factors.get(name, ONSET_BLEND))
        arm.pose.bones[name].rotation_quaternion = q
        arm.pose.bones[name].keyframe_insert(data_path="rotation_quaternion")
    for name in LEFT:
        arm.pose.bones[name].rotation_quaternion = left_rest[name].copy()
        arm.pose.bones[name].keyframe_insert(data_path="rotation_quaternion")


# f0: neutral (left AND right, incl. fingers as in HELLO rest)
scene.frame_set(F0)
bpy.context.view_layer.update()
pose_bones({n: 0.0 for n in RIGHT})
# f10: onset near lips — reduced salute, flat hand inherited from salute handshape
scene.frame_set(F_ONSET)
bpy.context.view_layer.update()
pose_bones({n: ONSET_BLEND for n in RIGHT})
# f20: stroke down-forward of lips
scene.frame_set(F_STROKE)
bpy.context.view_layer.update()
pose_bones({n: STROKE_BLEND for n in RIGHT})
# f40: return neutral (clean AvatarController crossfade to ASL_NEUTRAL)
scene.frame_set(F_END)
bpy.context.view_layer.update()
pose_bones({n: 0.0 for n in RIGHT})

bpy.ops.wm.save_as_mainfile(filepath=SAVE)
print(f"CANDIDATE {CLIP} RETARGETED (v2, HELLO-derived) -> {SAVE}")
