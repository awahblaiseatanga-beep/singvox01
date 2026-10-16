import bpy
import math
import mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v3.glb")

arm = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm = obj
        break

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

# Clear to Rest Pose (this strips the baked ASL_HELLO from the matrices)
for pb in arm.pose.bones:
    pb.matrix_basis = mathutils.Matrix.Identity(4)

def get_bone(name):
    for pb in arm.pose.bones:
        if name in pb.name or pb.name in name: return pb
    return arm.pose.bones[name.split(':')[-1]]

def get_world_vec(pb):
    mat = arm.matrix_world @ pb.matrix
    head = mat @ pb.bone.head_local
    tail = mat @ pb.bone.tail_local
    return (tail - head).normalized()

print("=== V3.GLB BONE AXES INVESTIGATION ===")

b_arm = get_bone('LeftArm')
b_fore = get_bone('LeftForeArm')
b_hand = get_bone('LeftHand')

print(f"Rest LeftArm: {get_world_vec(b_arm)}")
print(f"Rest LeftForeArm: {get_world_vec(b_fore)}")

def test_bone_axis(pb, name):
    pb.rotation_mode = 'XYZ'
    print(f"\n[{name}] Local Rotations -> World Vectors:")
    for axis in ['X', 'Y', 'Z']:
        for degrees in [30]:
            pb.rotation_euler = (0,0,0)
            rot = [0,0,0]
            rot[['X','Y','Z'].index(axis)] = math.radians(degrees)
            pb.rotation_euler = rot
            bpy.context.view_layer.update()
            
            vec = get_world_vec(pb)
            print(f"  + {degrees}deg on {axis} -> Vec: {vec.x:.2f}, {vec.y:.2f}, {vec.z:.2f}")
    
    pb.rotation_euler = (0,0,0)
    bpy.context.view_layer.update()

test_bone_axis(b_arm, 'LeftArm')
test_bone_axis(b_fore, 'LeftForeArm')
test_bone_axis(b_hand, 'LeftHand')

# Measure Hand Palm / Fingers natively
print("\n[LeftHand] Rest Orientations:")
mat = arm.matrix_world @ b_hand.matrix
fingers = (mat.to_3x3() @ mathutils.Vector((0,1,0))).normalized()
palm = (mat.to_3x3() @ mathutils.Vector((0,0,-1))).normalized() # Testing standard Z palm
print(f"  Local +Y (Fingers) -> World: {fingers.x:.2f}, {fingers.y:.2f}, {fingers.z:.2f}")
print(f"  Local -Z (Palm?) -> World: {palm.x:.2f}, {palm.y:.2f}, {palm.z:.2f}")
