import bpy
import math

def inspect_file(filepath):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ext = filepath.split('.')[-1].lower()
    
    if ext == 'fbx':
        bpy.ops.import_scene.fbx(filepath=filepath)
    elif ext == 'glb':
        bpy.ops.import_scene.gltf(filepath=filepath)
        
    arm = None
    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            arm = obj
            break
            
    if not arm:
        print(f"[{filepath}] NO ARMATURE FOUND!")
        return
        
    print(f"\n--- INSPECTION: {filepath} ---")
    print(f"Armature Name: {arm.name}")
    
    # Active Action check
    if arm.animation_data and arm.animation_data.action:
        print(f"Active Action: {arm.animation_data.action.name}")
    else:
        print("Active Action: None")
        
    # Check Rest Pose vs Active Pose
    bones = ['mixamorig4:LeftArm', 'mixamorig4:RightArm', 'mixamorig4:LeftForeArm', 'mixamorig4:RightForeArm']
    if ext == 'fbx': # FBX usually doesn't have the colon prefix unless imported via glTF later it was added?
        # Let's search inside the armature
        search_bones = ['LeftArm', 'RightArm']
        for b in arm.data.bones:
            if 'mixamorig' in b.name:
                bones = ['mixamorig:LeftArm', 'mixamorig:RightArm', 'mixamorig:LeftForeArm', 'mixamorig:RightForeArm']
                break
                
    # Also check if it's straight Mixamo names
    actual_bones = []
    for bn in bones:
        if bn in arm.pose.bones:
            actual_bones.append(bn)
        elif bn.replace('mixamorig4:', 'mixamorig:') in arm.pose.bones:
            actual_bones.append(bn.replace('mixamorig4:', 'mixamorig:'))
        elif bn.split(':')[-1] in arm.pose.bones:
             actual_bones.append(bn.split(':')[-1])
            
    print("\n[Bone Rotations: XYZ Euler]")
    for bn in actual_bones:
        pose_b = arm.pose.bones[bn]
        
        # Determine if there's any active pose offset over the REST pose
        # matrix_basis is the local pose transform containing translation/rotation/scale relative to REST
        euler = pose_b.matrix_basis.to_euler('XYZ')
        
        print(f"{bn}: Pose Offset: ({math.degrees(euler.x):.2f}, {math.degrees(euler.y):.2f}, {math.degrees(euler.z):.2f})")
        
        # Check actual world angle of the Rest Pose bone vs armature
        rest_mat = arm.data.bones[bn].matrix_local
        print(f"   Rest Matrix Translation: {rest_mat.translation}")

inspect_file(r"d:\Singvox\Singvox\avatar\models\Ch41_nonPBR.fbx")
inspect_file(r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v3.glb")
