import numpy as np
import sys

feature_file = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted\0022932153577568393-HELLO_features.npy"
try:
    arr = np.load(feature_file)
    print(f"Loaded {feature_file}")
    print(f"Shape: {arr.shape}") # Expecting (Frames, 366)
    
    # Slice the channels based on extract_dataset.py assumptions:
    # 0:63 -> Left Hand (21 points * 3)
    # 63:126 -> Right Hand (21 points * 3)
    # 126:126+165 -> Pose (33 points * 5)
    
    frames = arr.shape[0]
    
    def analyze_block(name, block, coords_per_pt=3):
        print(f"\n--- {name} Block ---")
        pts = block.shape[1] // coords_per_pt
        print(f"Contains {pts} points ({coords_per_pt}D axes)")
        
        # Check missing (all zeros)
        zero_frames = np.sum(np.all(block == 0, axis=1))
        print(f"Frames utterly missing/zeroed: {zero_frames} out of {frames}")

        if zero_frames == frames:
            print(f"X range: N/A, Y range: N/A, Z range: N/A")
            return
            
        x_data = block[:, 0::coords_per_pt]
        y_data = block[:, 1::coords_per_pt]
        z_data = block[:, 2::coords_per_pt]

        print(f"X range: [{np.min(x_data):.5f}, {np.max(x_data):.5f}], variance={np.var(x_data):.5e}")
        print(f"Y range: [{np.min(y_data):.5f}, {np.max(y_data):.5f}], variance={np.var(y_data):.5e}")
        print(f"Z range: [{np.min(z_data):.5f}, {np.max(z_data):.5f}], variance={np.var(z_data):.5e}")

    analyze_block("Left Hand", arr[:, 0:63], 3)
    analyze_block("Right Hand", arr[:, 63:126], 3)
    analyze_block("Pose", arr[:, 126:126+165], 5) # (X,Y,Z,visibility,presence)

except Exception as e:
    print(f"Error: {e}")
