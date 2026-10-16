import bpy
import numpy as np

def setup_ik_baking():
    armature = bpy.data.objects.get("Armature") or bpy.data.objects.get("Armature.001")
    
    # Ensure unhidden and selected
    armature.hide_viewport = False
    armature.hide_set(False)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.transforms_clear()
    
    def apply_ik(hand_bone, wrist_target, elbow_pole, pole_angle, chain_len=2):
        pb = armature.pose.bones[hand_bone]
        con = pb.constraints.new('IK')
        con.target = bpy.data.objects[wrist_target]
        con.pole_target = bpy.data.objects[elbow_pole]
        con.chain_count = chain_len
        con.pole_angle = pole_angle
        # Give IK some iterations
        con.iterations = 100
        return con

    # Clear old constraints
    for pb in armature.pose.bones:
        for c in pb.constraints:
            pb.constraints.remove(c)
            
    # For Mixamo rigs, pole angle determines elbow direction.
    con_l = apply_ik("mixamorig4:LeftHand", "MP_Trace_Left_Wrist", "MP_Trace_Left_Elbow", -1.57) # -90 deg guess
    con_r = apply_ik("mixamorig4:RightHand", "MP_Trace_Right_Wrist", "MP_Trace_Right_Elbow", 1.57)

setup_ik_baking()
