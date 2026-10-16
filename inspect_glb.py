import json
import struct
import sys

def inspect_glb(glb_path):
    with open(glb_path, 'rb') as f:
        magic = f.read(4)
        if magic != b'glTF':
            print("Not a GLTF file!")
            return
        version, length = struct.unpack('<II', f.read(8))
        chunk_length, chunk_type = struct.unpack('<II', f.read(8))
        
        if chunk_type != 0x4E4F534A: # 'JSON'
            print("First chunk is not JSON")
            return
            
        json_data = f.read(chunk_length).decode('utf-8')
        gltf = json.loads(json_data)
        
        print("====== GLB INSPECTION ======")
        print(f"Nodes (Bones/Transforms) Count: {len(gltf.get('nodes', []))}")
        print(f"Meshes Count: {len(gltf.get('meshes', []))}")
        print(f"Materials Count: {len(gltf.get('materials', []))}")
        
        animations = gltf.get('animations', [])
        print(f"Animations Count: {len(animations)}")
        anim_names = [a.get('name', 'Unknown') for a in animations]
        print(f"Animation Names: {anim_names}")
        
        has_morph = False
        morph_count = 0
        for m in gltf.get('meshes', []):
            if 'weights' in m or any('targets' in p for p in m.get('primitives', [])):
                has_morph = True
                morph_count += len(m.get('weights', []))
        
        print(f"Face / Morph Targets Available: {has_morph}")
        print(f"Morph Target Count: {morph_count}")
        
if __name__ == '__main__':
    inspect_glb(sys.argv[1])
