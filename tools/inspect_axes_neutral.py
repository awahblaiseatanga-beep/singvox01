import bpy
import math
import mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"d:\Singvox\Singvox\avatar\models\Ch41_nonPBR.fbx")

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

def get_bone(bname):
    for pb in arm.pose.bones:
        if bname in pb.name or pb.name in bname: return pb
    return arm.pose.bones[bname.split(':')[-1]]

l_arm = get_bone('LeftArm')
l_fore = get_bone('LeftForeArm')
l_hand = get_bone('LeftHand')

print("--- RAW REST VECTORS (WORLD SPACE) ---")
# To get the vector of the bone in world space, we subtract head from tail
def bone_vec(pb):
    mat = arm.matrix_world @ pb.matrix
    head = mat @ pb.bone.head_local
    tail = mat @ pb.bone.tail_local
    return (tail - head).normalized()

print(f"LeftArm Rest Dir: {bone_vec(l_arm)}")
print(f"LeftForeArm Rest Dir: {bone_vec(l_fore)}")
print(f"LeftHand Rest Dir: {bone_vec(l_hand)}")

print("\n--- MEASURING BASE ROTATION OFFSETS ---")
# If we rotate LeftArm on X, Y, Z, where does it point?
pb = l_arm
pb.rotation_mode = 'XYZ'
for axis in ['X', 'Y', 'Z']:
    for val in [-30, 30]:
        rot = [0,0,0]
        rot[['X','Y','Z'].index(axis)] = math.radians(val)
        pb.rotation_euler = rot
        bpy.context.view_layer.update()
        print(f"LeftArm Rotate {axis} by {val} deg -> Dir: {bone_vec(l_arm)}")
        
pb.rotation_euler = (0,0,0)
bpy.context.view_layer.update()

pb = l_fore
pb.rotation_mode = 'XYZ'
for axis in ['X', 'Y', 'Z']:
    for val in [-30, 30]:
        rot = [0,0,0]
        rot[['X','Y','Z'].index(axis)] = math.radians(val)
        pb.rotation_euler = rot
        bpy.context.view_layer.update()
        print(f"LeftForeArm Rotate {axis} by {val} deg -> Dir: {bone_vec(l_fore)}")

pb.rotation_euler = (0,0,0)
bpy.context.view_layer.update()

# Measure Hand roll (palm direction)
# To measure palm, the +Z or -Z of the hand bone typically points out of the palm or back of hand.
def palm_dir(pb):
    mat = arm.matrix_world @ pb.matrix
    # In Mixamo, +Y is down the finger. +Z or +X is the Palm. Let's see Z.
    vec = (mat.to_3x3() @ mathutils.Vector((0,0,1))).normalized()
    return vec

print(f"\nLeftHand Rest Palm Z-Dir: {palm_dir(l_hand)}")
pb = l_fore 
pb.rotation_mode = 'XYZ'
for val in [-90, 90]:
    pb.rotation_euler = (0, math.radians(val), 0) # Roll
    bpy.context.view_layer.update()
    print(f"LeftForeArm Rotate Y (roll) by {val} deg -> Palm Z-Dir: {palm_dir(l_hand)}")

