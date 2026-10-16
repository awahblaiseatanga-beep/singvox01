import bpy
import logging

logging.basicConfig(level=logging.ERROR)

bpy.ops.wm.read_homefile(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v2.glb")

junk = ["Icosphere", "Cube", "Chest_Target", "LeftHip", "RightHip", "Hand_Target", "MP_Trace"]
for j in junk:
    for obj in bpy.data.objects:
        if j in obj.name:
            bpy.data.objects.remove(obj, do_unlink=True)

arm = bpy.data.objects.get("Armature")
if arm:
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    if 'ASL_HELLO' in bpy.data.actions:
        # Guarantee it exports by setting active
        if not arm.animation_data:
            arm.animation_data_create()
        arm.animation_data.action = bpy.data.actions.get('ASL_HELLO')
        print("Restored ASL_HELLO track binding!")

bpy.ops.export_scene.gltf(
    filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v3.glb",
    export_format='GLB',
    use_selection=False,
    export_animations=True,
    export_rest_position_armature=False,
    export_apply=True,
    export_tangents=False
)
print("SUCCESS V3 FINAL SCRUB")
