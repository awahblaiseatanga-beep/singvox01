import bpy
import numpy as np
import sys
import math
sys.path.append(r"d:\Singvox\Singvox\tools")
from landmark_to_rig import LandmarkConversion

def apply():
    arm = bpy.data.objects.get("Armature") or bpy.data.objects.get("Armature.001")
    
    # Ensure active context implicitly natively
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.transforms_clear()
    
    features = np.load(r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted\0022932153577568393-HELLO_features.npy")
    
    action = bpy.data.actions.new("ASL_HELLO")
    if not arm.animation_data:
        arm.animation_data_create()
    arm.animation_data.action = action
    
    def get_body_pt(frame, idx):
        offset = 126 + idx*5
        return np.array([frame[offset], frame[offset+1], frame[offset+2]])
        
    origin = arm.pose.bones["mixamorig4:RightShoulder"].head.copy()
    
    def create_tracker(name):
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.empty_add(type='PLAIN_AXES')
        empty = bpy.context.active_object
        empty.name = name
        bpy.context.view_layer.objects.active = arm
        bpy.ops.object.mode_set(mode='POSE')
        return empty
        
    e_elbow_l = create_tracker("T_Elbow_L")
    e_wrist_l = create_tracker("T_Wrist_L")
    
    b_arm_l = arm.pose.bones.get("mixamorig4:LeftArm")
    con1 = b_arm_l.constraints.new('DAMPED_TRACK')
    con1.target = e_elbow_l
    
    b_forearm_l = arm.pose.bones.get("mixamorig4:LeftForeArm")
    con2 = b_forearm_l.constraints.new('DAMPED_TRACK')
    con2.target = e_wrist_l
    
    for f_idx in range(len(features)):
        dat = features[f_idx]
        conv = LandmarkConversion(dat)
        
        pt_elb = get_body_pt(dat, 13)
        pt_wst = get_body_pt(dat, 15)
        
        bx_e = origin.x + (-pt_elb[0] * 0.3)
        by_e = origin.y + (pt_elb[2] * 0.3)
        bz_e = origin.z + (-pt_elb[1] * 0.3)
        
        bx_w = origin.x + (-pt_wst[0] * 0.4)
        by_w = origin.y + (pt_wst[2] * 0.4)
        bz_w = origin.z + (-pt_wst[1] * 0.4)
        
        e_elbow_l.location = (bx_e, by_e, bz_e)
        e_wrist_l.location = (bx_w, by_w, bz_w)
        
        e_elbow_l.keyframe_insert(data_path="location", frame=f_idx)
        e_wrist_l.keyframe_insert(data_path="location", frame=f_idx)
        
        fingers = conv.get_finger_segment_angles("LEFT")
        if fingers:
            for finger_name, angles in fingers.items():
                if finger_name == "Thumb": continue
                for i in range(1, min(len(angles)+1, 4)):
                    bone = arm.pose.bones.get(f"mixamorig4:LeftHand{finger_name}{i}")
                    if bone:
                        bone.rotation_mode = 'XYZ'
                        bone.rotation_euler[2] = angles[i-1] * -0.8
                        bone.keyframe_insert(data_path="rotation_euler", frame=f_idx)

    # Keyframe explicitly derived wrist rotations natively mathematically locking zero SO3 bounds
    lw = arm.pose.bones["mixamorig4:LeftHand"]
    lw.rotation_mode = 'QUATERNION'
    rw = arm.pose.bones["mixamorig4:RightHand"]
    rw.rotation_mode = 'QUATERNION'
    lw.keyframe_insert(data_path="rotation_quaternion", frame=0)
    rw.keyframe_insert(data_path="rotation_quaternion", frame=0)
    lw.keyframe_insert(data_path="rotation_quaternion", frame=len(features)-1)
    rw.keyframe_insert(data_path="rotation_quaternion", frame=len(features)-1)

    # Bake purely explicit mechanical transforms (NOT IK) natively to keyframes avoiding visual artifacts
    bpy.ops.nla.bake(
        frame_start=0, frame_end=len(features)-1,
        only_selected=False, visual_keying=True,
        clear_constraints=True, use_current_action=True, bake_types={'POSE'}
    )
    
    bpy.context.view_layer.objects.active = arm
    
    track = arm.animation_data.nla_tracks.new()
    track.name = "ASL_HELLO"
    track.strips.new("ASL_HELLO", 0, arm.animation_data.action)
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects.remove(e_elbow_l, do_unlink=True)
    bpy.data.objects.remove(e_wrist_l, do_unlink=True)
    
    import logging
    logging.getLogger("glTF-Blender-IO").setLevel(logging.CRITICAL)
    bpy.ops.export_scene.gltf(
        filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v4_HELLO.glb",
        export_format='GLB',
        use_selection=False,
        export_animations=True,
        export_rest_position_armature=False,
        export_apply=True
    )
    print("V4 EXPORT SUCCESSFUL")

if __name__ == "__main__":
    apply()
