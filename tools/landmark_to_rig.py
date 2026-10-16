import numpy as np
import math

class LandmarkConversion:
    """
    Transforms flattened 366-D ASL-Citizen MediaPipe tensor frames into local rigid SO(3) rotations.
    
    Tensor mapping limits:
    - [0:63]:   Left Hand (21 * (x,y,z))
    - [63:126]: Right Hand (21 * (x,y,z))
    - [126:165]: Body Pose
    """
    
    def __init__(self, frame_data):
        self.frame = frame_data
        self.left_hand = frame_data[:63].reshape(21, 3)
        self.right_hand = frame_data[63:126].reshape(21, 3)
        self.body = frame_data[126:291].reshape(33, 5)

    def is_hand_present(self, hand="LEFT"):
        h = self.left_hand if hand == "LEFT" else self.right_hand
        return np.sum(np.abs(h)) > 0.001
        
    def _safe_normalize(self, v):
        norm = np.linalg.norm(v)
        if norm < 1e-6:
            return np.array([0, 0, 0])
        return v / norm

    def get_palm_basis(self, hand="LEFT"):
        """
        Derives an orthonormal coordinate basis [X, Y, Z] describing the palm's spatial orientation.
        Y typically points from wrist to middle finger.
        X points across the knuckles.
        Z is the palm normal (Outward).
        """
        if not self.is_hand_present(hand):
            return np.eye(3)
            
        h = self.left_hand if hand == "LEFT" else self.right_hand
        wrist = h[0]
        index_mcp = h[5]
        middle_mcp = h[9]
        pinky_mcp = h[17]
        
        # Determine strict Y-axis (Direction of hand flow)
        y_vec = self._safe_normalize(middle_mcp - wrist)
        
        # Determine structural pseudo-X across knuckles
        vec_across = self._safe_normalize(index_mcp - pinky_mcp)
        
        # Z normal via cross product. 
        # *LIMITATION*: The dataset's Z bounds are ~1e-7. Cross products will inherently lock to purely (0,0,\pm 1) plane natively!
        z_vec = self._safe_normalize(np.cross(vec_across, y_vec))
        if np.sum(np.abs(z_vec)) == 0:
            z_vec = np.array([0, 0, 1])
            
        # Reforge exact orthogonal X
        x_vec = self._safe_normalize(np.cross(y_vec, z_vec))
        
        # Basis Matrix
        basis = np.column_stack((x_vec, y_vec, z_vec))
        return basis

    def get_finger_segment_angles(self, hand="LEFT"):
        """
        Extracts structural bending angles for the fingers to map directly to bone axes.
        Since Z depth is fundamentally flattened globally, we can mathematically fallback to 2D cosine bounds safely.
        """
        angles = {}
        if not self.is_hand_present(hand):
            return angles
            
        h = self.left_hand if hand == "LEFT" else self.right_hand
        
        # MediaPipe standard indices mapping
        fingers = {
            "Thumb": [0, 1, 2, 3, 4],
            "Index": [0, 5, 6, 7, 8],
            "Middle": [0, 9, 10, 11, 12],
            "Ring": [0, 13, 14, 15, 16],
            "Pinky": [0, 17, 18, 19, 20]
        }
        
        def angle_between(v1, v2):
            v1_u = self._safe_normalize(v1)
            v2_u = self._safe_normalize(v2)
            c = np.dot(v1_u, v2_u)
            if np.isnan(c): return 0.0
            return math.acos(np.clip(c, -1.0, 1.0))
            
        for name, indices in fingers.items():
            angles[name] = []
            for i in range(1, len(indices) - 1):
                p0 = h[indices[i-1]]
                p1 = h[indices[i]]
                p2 = h[indices[i+1]]
                
                vec_in = p1 - p0
                vec_out = p2 - p1
                bend = angle_between(vec_in, vec_out)
                angles[name].append(bend)
                
        return angles

if __name__ == "__main__":
    def run_tests():
        print("--- RUNNING DIAGNOSTICS ---")
        tensor_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted\0022932153577568393-HELLO_features.npy"
        f = np.load(tensor_path)
        
        # Test Frame 15 (Active Left Hand)
        v = LandmarkConversion(f[15])
        
        print("Left Hand Active:", v.is_hand_present("LEFT"))
        print("Right Hand Active:", v.is_hand_present("RIGHT"))
        
        l_basis = v.get_palm_basis("LEFT")
        print("\nLeft Palm Basis Matrix:\n", l_basis)
        
        l_fingers = v.get_finger_segment_angles("LEFT")
        print("\nLeft Finger Inner Bend Angles (Radians):")
        for f_name, angles in l_fingers.items():
            print(f"  {f_name}: {[round(a, 3) for a in angles]}")
            
    run_tests()
