import bpy
import logging

logging.basicConfig(level=logging.INFO)

print("CLEARING SCENE")
bpy.ops.wm.read_homefile(use_empty=True)

print("IMPORTING V2 GLB")
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\avatar\exports\SignVox_Female_v2.glb")

print("PURGING JUNK")
junk = ["Icosphere", "Icosphere.001", "Cube", "Chest_Target_+Y", "Chest_Target_-Y", "LeftHip_Target", "RightHip_Target", "RightHand_Target", "MP_Trace_Left_Shoulder", "MP_Trace_Right_Shoulder", "MP_Trace_Left_Elbow", "MP_Trace_Right_Elbow", "MP_Trace_Left_Wrist", "MP_Trace_Right_Wrist"]
for j in junk:
    obj = bpy.data.objects.get(j)
    if obj: 
        bpy.data.objects.remove(obj, do_unlink=True)
        print(f"Removed {j}")

arm = bpy.data.objects.get("Armature")
if arm:
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    print("Activated Armature")
    print("Actions Attached:", [a.name for a in bpy.data.actions])

print("EXPORTING V3 GLB")
bpy.ops.export_scene.gltf(
    filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v3.glb",
    export_format='GLB',
    use_selection=False,
    export_animations=True,
    export_rest_position_armature=False,
    export_apply=True
)
print("SUCCESS!")
