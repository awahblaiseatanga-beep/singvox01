import bpy
import numpy as np

def run():
    features = np.load(r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted\0022932153577568393-HELLO_features.npy")
    
    target_indices = {
        "Left_Shoulder": 126 + 11*5,
        "Right_Shoulder": 126 + 12*5,
        "Left_Elbow": 126 + 13*5,
        "Right_Elbow": 126 + 14*5,
        "Left_Wrist": 126 + 15*5,
        "Right_Wrist": 126 + 16*5
    }
    
    for obj in bpy.data.objects:
        if obj.name.startswith("MP_Trace_"):
            bpy.data.objects.remove(obj)
            
    empties = {}
    for name in target_indices.keys():
        bpy.ops.object.empty_add(type='SPHERE', radius=0.04)
        empty = bpy.context.active_object
        empty.name = "MP_Trace_" + name
        # Setup specific colors for visual clarity
        mat = bpy.data.materials.new(name="Mat_" + name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        if "Left" in name: 
            bsdf.inputs['Base Color'].default_value = (1, 0, 0, 1) # Red
        else: 
            bsdf.inputs['Base Color'].default_value = (0, 1, 0, 1) # Green
        empty.active_material = mat
        empties[name] = empty
        
    scene = bpy.context.scene
    scene.frame_start = 0
    scene.frame_end = len(features) - 1
    
    # Measure directly from avatar rig
    armature = bpy.data.objects.get("Armature") or bpy.data.objects.get("Armature.001")
    l_shoulder = armature.pose.bones["mixamorig4:LeftShoulder"].head
    r_shoulder = armature.pose.bones["mixamorig4:RightShoulder"].head
    l_arm = armature.pose.bones["mixamorig4:LeftArm"].head
    r_arm = armature.pose.bones["mixamorig4:RightArm"].head
    
    l_shoulder_world = armature.matrix_world @ l_arm
    r_shoulder_world = armature.matrix_world @ r_arm
    
    origin = (l_shoulder_world + r_shoulder_world) / 2.0
    shoulder_dist = (l_shoulder_world - r_shoulder_world).length
    
    print(f"Origin computed: {origin}, Shoulder Dist: {shoulder_dist}")
    
    for f in range(len(features)):
        frame_data = features[f]
        for name, idx in target_indices.items():
            # MediaPipe normalized array bounds:
            x = frame_data[idx]
            y = frame_data[idx+1]
            z = frame_data[idx+2]
            
            # Avatar faces -Y in Blender world.
            # MediaPipe X: Left of image (so avatar's Right) is -X, right of image is +X.
            # Wait, in extract script: `center_x = (s_left[0] + s_right[0]) / 2.0`
            # For MediaPipe: s_left is index 11 (user's right side of image).
            # So if x > 0, it means it is towards the user's left arm.
            # In Blender facing -Y, +X is left arm. So bx = origin.x + x * shoulder_dist
            bx = origin.x + (-x * shoulder_dist)
            bz = origin.z + (-y * shoulder_dist)
            by = origin.y + (z * shoulder_dist)
            
            empties[name].location = (bx, by, bz)
            empties[name].keyframe_insert(data_path="location", frame=f)

    # Insert action name so we can save it later
    print("Empties animated for", len(features), "frames.")

run()
