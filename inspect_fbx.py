import re
import sys

def extract_bones(filepath):
    print(f"\n--- Inspecting {filepath} ---")
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
            
        strings = re.findall(b'[a-zA-Z0-9_:]{4,}', data)
        strings = [s.decode('ascii', errors='ignore') for s in strings]
        
        # look for mixamorig or bones
        bones = set()
        for s in strings:
            if "mixamorig" in s.lower() or "bone" in s.lower():
                bones.add(s)
                
        print(f"Found {len(bones)} unique bones/nodes related to 'mixamorig' or 'bone':")
        for b in sorted(list(bones)):
            # Filter out some garbage if any
            if "mixamorig" in b.lower():
                print("  =>", b)
        
        # Also check for animation actions
        actions = [s for s in strings if 'AnimStack' in s or 'AnimLayer' in s or 'Take' in s]
        print(f"Found {len(actions)} strings related to Animations.")
            
    except Exception as e:
        print("Error:", e)
        
extract_bones(r"d:\Singvox\Singvox\avatar\models\Ch41_nonPBR.fbx")
extract_bones(r"d:\Singvox\Singvox\avatar\models\Ch12_nonPBR.fbx")
