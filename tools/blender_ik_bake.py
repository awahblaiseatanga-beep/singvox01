import bpy
import os

def bake_and_export():
    armature = bpy.data.objects.get("Armature") or bpy.data.objects.get("Armature.001")
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode='POSE')
    
    # Bake the action to raw keyframes and remove constraints
    bpy.ops.nla.bake(frame_start=0, frame_end=30, step=1,
                    only_selected=False, visual_keying=True,
                    clear_constraints=True, use_current_action=True,
                    bake_types={'POSE'})
    
    # Rename the action so the web app recognizes it easily
    if armature.animation_data and armature.animation_data.action:
        armature.animation_data.action.name = "ASL_HELLO"
        
    export_path = r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v2.glb"
    
    # Keep the default options, but make sure to export animation
    bpy.ops.export_scene.gltf(
        filepath=export_path,
        export_format='GLB',
        use_selection=False,
        export_animations=True,
        export_rest_position_armature=False,
        export_apply=True
    )
    print("Action baked and exported to", export_path)

bake_and_export()
