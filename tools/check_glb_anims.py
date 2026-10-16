import bpy
import sys

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v6_Neutral.glb")

print("=== ANIMATIONS IN V6 ===")
for action in bpy.data.actions:
    print(f"Action: {action.name}, Frames: {action.frame_range[0]} to {action.frame_range[1]}")
