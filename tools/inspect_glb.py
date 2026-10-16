import bpy
import sys

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v3.glb")

arm = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm = obj
        break

if not arm:
    print("NO ARMATURE")
    sys.exit()

# We want to dump all bone names to look for 'Index' and 'mixamorig' namespaces
for b in arm.data.bones:
    if "Index" in b.name or "Mixamorig" in b.name or "mixamorig" in b.name:
        print(f"BONE_DUMP: {b.name}")
