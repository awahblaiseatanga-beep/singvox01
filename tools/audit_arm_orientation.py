import bpy
import math

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

# Check for twist bones
twist_bones = [b.name for b in arm.data.bones if 'Twist' in b.name or 'Roll' in b.name]
print(f"Twist Bones Found: {twist_bones}")

def analyze_bone(b_name):
    if b_name not in arm.pose.bones:
        print(f"Bone {b_name} missing.")
        return
    
    pose_b = arm.pose.bones[b_name]
    edit_b = arm.data.bones[b_name]
    
    p_name = pose_b.parent.name if pose_b.parent else 'None'
    
    # Bone tail - head gives the Y axis direction in local space
    # which is the bone's primary length axis.
    v = edit_b.tail_local - edit_b.head_local
    length = v.length
    
    # We want to know how the Local Axes orient relative to the World or Parent.
    # We can inspect the local matrix of the pose bone.
    mat_local = pose_b.matrix_basis
    
    print(f"Bone: {b_name}")
    print(f"  Parent: {p_name}")
    print(f"  Length: {length:.4f}")
    
    # Determine what global axis matches the bone's Y axis
    # edit_b.matrix.to_3x3() gives the mapping from bone local space to armature space
    y_axis = edit_b.vector.normalized()
    print(f"  Default Y-Axis points towards Armature (x,y,z): {y_axis.x:.2f}, {y_axis.y:.2f}, {y_axis.z:.2f}")

bones_to_check = [
    'mixamorig4:LeftShoulder', 'mixamorig4:LeftArm', 'mixamorig4:LeftForeArm', 'mixamorig4:LeftHand',
    'mixamorig4:RightShoulder', 'mixamorig4:RightArm', 'mixamorig4:RightForeArm', 'mixamorig4:RightHand'
]

print("\n--- BONE AUDIT ---")
for b in bones_to_check:
    analyze_bone(b)

print("Blender script complete.")
