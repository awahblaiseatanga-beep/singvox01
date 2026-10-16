import json
import struct
import sys
import math

def check_hierarchy(glb_path):
    with open(glb_path, 'rb') as f:
        magic = f.read(4)
        if magic != b'glTF':
            print("Not GLTF")
            return
        version, length = struct.unpack('<II', f.read(8))
        chunk_length, chunk_type = struct.unpack('<II', f.read(8))
        
        json_data = f.read(chunk_length).decode('utf-8')
        gltf = json.loads(json_data)
        
        nodes = gltf.get('nodes', [])
        
        # Build map of names to indices
        name_map = {}
        for i, n in enumerate(nodes):
            name = n.get('name', '')
            # Handle Mixamo namespace
            if 'LeftHand' in name or 'RightHand' in name:
               name_map[name.split(':')[-1] if ':' in name else name] = n
               
        print("--- Node Local Translations ---")
        def print_node_stats(name):
           node = name_map.get(name)
           if not node:
               print(f"{name} not found")
               return
           
           t = node.get('translation', [0, 0, 0])
           r = node.get('rotation', [0, 0, 0, 1])
           s = node.get('scale', [1, 1, 1])
           length = math.sqrt(t[0]**2 + t[1]**2 + t[2]**2)
           print(f"{name}:")
           print(f"  Translation: {t} (Len: {length:.6f})")
           print(f"  Rotation: {r}")
           print(f"  Scale: {s}")
           
        for b in ['LeftHand', 'LeftHandIndex1', 'LeftHandIndex2', 'LeftHandIndex3', 'LeftHandIndex4',
                  'RightHand', 'RightHandIndex1', 'RightHandIndex2', 'RightHandIndex3', 'RightHandIndex4']:
            print_node_stats(b)
            
if __name__ == '__main__':
    check_hierarchy(sys.argv[1])
