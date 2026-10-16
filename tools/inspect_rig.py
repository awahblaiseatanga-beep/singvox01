import bpy
import math

# Clean scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# Import untouched FBX
bpy.ops.import_scene.fbx(filepath=r"d:\Singvox\Singvox\avatar\models\Ch41_nonPBR.fbx")

arm = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm = obj
        break

if not arm:
    print("NO ARMATURE FOUND IN FBX")
    exit()

print(f"\n--- ARMATURE OBJECT ---")
print(f"Name: {arm.name}")
print(f"Transform Location: {arm.location}")
print(f"Transform Rotation Euler: {arm.rotation_euler}")
print(f"Transform Scale: {arm.scale}")

# We need EDIT mode to view proper rest pose bone rolls securely
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')

print(f"\n--- BONE HIERARCHY & ROLLS (EDIT MODE REST POSE) ---")

for b in arm.data.edit_bones:
    if "RightArm" in b.name or "RightForeArm" in b.name or "RightHand" in b.name or "RightShoulder" in b.name:
        print(f"\nBone: {b.name}")
        print(f"Parent: {b.parent.name if b.parent else 'None'}")
        print(f"Head (World): [{b.head.x:.4f}, {b.head.y:.4f}, {b.head.z:.4f}]")
        print(f"Tail (World): [{b.tail.x:.4f}, {b.tail.y:.4f}, {b.tail.z:.4f}]")
        print(f"Roll (Radians): {b.roll:.4f}")
        vec = b.tail - b.head
        print(f"Local Y (Tail-Head): [{vec.x:.4f}, {vec.y:.4f}, {vec.z:.4f}]")

bpy.ops.object.mode_set(mode='POSE')
print(f"\n--- BONE CONSTRAINTS ---")
for b in arm.pose.bones:
    if len(b.constraints) > 0:
        print(f"Bone {b.name} has constraints: {[c.type for c in b.constraints]}")

print("\nRIG AUDIT COMPLETE")
