import bpy
import numpy as np

def run():
    features = np.load(r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted\0022932153577568393-HELLO_features.npy")
    # frame limit mapping: 31 frames, 10 FPS
    
    # 0..62: Left Hand (21x3)
    # 63..125: Right Hand (21x3)
    # 126..290: Pose (33x5)
    # 291..365: Face (25x3)
    
    # We want to track Left and Right Shoulder, Elbow, Wrist
    target_indices = {
        "Left_Shoulder": 126 + 11*5,
        "Right_Shoulder": 126 + 12*5,
        "Left_Elbow": 126 + 13*5,
        "Right_Elbow": 126 + 14*5,
        "Left_Wrist": 126 + 15*5,
        "Right_Wrist": 126 + 16*5
    }
    
    # Delete old tracing empties
    for obj in bpy.data.objects:
        if obj.name.startswith("MP_Trace_"):
            bpy.data.objects.remove(obj)
            
    # Create empties
    empties = {}
    for name in target_indices.keys():
        bpy.ops.object.empty_add(type='SPHERE', radius=0.05)
        empty = bpy.context.active_object
        empty.name = "MP_Trace_" + name
        empties[name] = empty
        
    scene = bpy.context.scene
    scene.frame_start = 0
    scene.frame_end = len(features) - 1
    
    # Avatar reference point: neck/chest area
    # In V2, A-Pose origin is at feet. Shoulders are approx Z=1.3
    # MediaPipe scale: shoulder distance.
    # Let's read shoulder distance in A-Pose roughly: 0.35 meters
    shoulder_dist = 0.35
    origin = (0.0, 0.0, 1.35)
    
    for f in range(len(features)):
        frame_data = features[f]
        
        for name, idx in target_indices.items():
            # MediaPipe is X=Right(from viewer, so left of signer?), Y=Down, Z=Forward(towards camera)
            # Actually X in MediaPipe: 0 is left of image, 1 is right of image.
            # So from signer's perspective, X=-Right, Y=-Up, Z=-Forward
            # Let's map MP(X, Y, Z) -> Blender (-X, -Z, -Y) or something
            x = frame_data[idx]
            y = frame_data[idx+1]
            z = frame_data[idx+2]
            
            # Map MediaPipe coordinates to Blender coordinates
            # Normalization scale implies distance is proportional to shoulder width
            bx = x * shoulder_dist
            bz = -y * shoulder_dist + origin[2]
            by = z * shoulder_dist
            
            empties[name].location = (bx, by, bz)
            empties[name].keyframe_insert(data_path="location", frame=f)

    print("Empties animated for", len(features), "frames.")

run()
