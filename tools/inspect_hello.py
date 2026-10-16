import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v6_Neutral.glb")

arm = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm = obj
        break

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

action = bpy.data.actions.get("ASL_HELLO")
if action:
    if not arm.animation_data: arm.animation_data_create()
    arm.animation_data.action = action

def get_world_pos(name):
    for pb in arm.pose.bones:
        if name in pb.name or pb.name in name:
            return arm.matrix_world @ pb.matrix @ pb.bone.head_local
    return None

import mathutils

def euler_from_matrix(mat):
    return [math.degrees(x) for x in mat.to_euler('XYZ')]
import math

print("\n=== ASL_HELLO MOTION TRACK ===")
for frame in range(0, 31, 5):
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    
    lh_pos = get_world_pos('LeftHand')
    rh_pos = get_world_pos('RightHand')
    head_pos = get_world_pos('Head')
    
    # Is the hand near the head?
    rh_dist = (rh_pos - head_pos).length
    print(f"F{frame:02d} | RightHand: [{rh_pos.x:.2f}, {rh_pos.y:.2f}, {rh_pos.z:.2f}] | Dist to Head: {rh_dist:.2f}")

