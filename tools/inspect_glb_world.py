import bpy
import json

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v3.glb")

arm = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm = obj
        break

if not arm:
    print("FATAL: No armature")
    exit(1)

out = {}
# Force scene update
bpy.context.view_layer.update()

def get_bone_loc(b_name):
    if b_name in arm.pose.bones:
        b = arm.pose.bones[b_name]
        # matrix is in object space, must map to world
        return arm.matrix_world @ b.head
    return None

out['Head'] = list(get_bone_loc('mixamorig4:Head') or [0,0,0])
out['Hips'] = list(get_bone_loc('mixamorig4:Hips') or [0,0,0])
out['LeftHand'] = list(get_bone_loc('mixamorig4:LeftHand') or [0,0,0])
from math import degrees

print("BONE WORLD COORDINATES:")
for k, v in out.items():
    print(f"{k}: X={v[0]:.3f} Y={v[1]:.3f} Z={v[2]:.3f}")

