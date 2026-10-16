import bpy
import sys
import os

def find_avatar_scene():
    armature = None
    meshes = []
    cameras_and_lights = []

    for obj in bpy.context.scene.objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH':
            meshes.append(obj)
        elif obj.type in ['CAMERA', 'LIGHT']:
            cameras_and_lights.append(obj)

    return armature, meshes, cameras_and_lights

def validate_avatar_scene(armature, meshes):
    if not armature:
        print("ERROR: No armature found in the scene! Ensure you have manually imported the FBX.", file=sys.stderr)
        sys.exit(1)
        
    if not meshes:
        print("ERROR: No meshes found in the scene!", file=sys.stderr)
        sys.exit(1)

    # Dictionary validation
    bones = {bone.name: bone for bone in armature.data.bones}
    
    print("--- VALIDATING ARMATURE SYSTEM ---")
    print(f"Armature Name: {armature.name}")
    print(f"Mesh Count: {len(meshes)}")
    print(f"Total Bone Count: {len(bones)}")

    has_actions = hasattr(bpy.data, "actions") and len(bpy.data.actions) > 0
    print(f"Animation Count: {len(bpy.data.actions) if has_actions else 0}")

    morph_count = 0
    for m in meshes:
        if m.data.shape_keys:
            morph_count += len(m.data.shape_keys.key_blocks) - 1
    print(f"Morph Targets Discovered: {morph_count}")

    # Check required bones
    required_bones = [
        "mixamorig4:LeftHand", 
        "mixamorig4:RightHand"
    ]
    
    fingers = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
    for side in ["LeftHand", "RightHand"]:
        for f in fingers:
            for num in [1, 2, 3]:
                required_bones.append(f"mixamorig4:{side}{f}{num}")

    missing = []
    fingers_found = 0
    for rb in required_bones:
        if rb not in bones:
            missing.append(rb)
        elif "Thumb" in rb or "Index" in rb or "Middle" in rb or "Ring" in rb or "Pinky" in rb:
            fingers_found += 1
            
    print(f"Finger Bones Found: {fingers_found}")

    if missing:
        print(f"ERROR: Armature is missing required canonical bones: {missing}", file=sys.stderr)
        sys.exit(1)

    print("VALIDATION SUCCESSFUL: Core skeleton and joints are intact.")
    return True

def export_glb(export_path, cameras_and_lights):
    # Remove unnecessary objects before export
    for cl in cameras_and_lights:
        bpy.data.objects.remove(cl, do_unlink=True)

    os.makedirs(os.path.dirname(export_path), exist_ok=True)
    print(f"Exporting to GLB: {export_path}")

    bpy.ops.export_scene.gltf(
        filepath=export_path,
        export_format='GLB',
        use_selection=False,
        export_apply=True,
        export_animations=True,
        export_skins=True,
        export_morph=True,
        export_materials='EXPORT',
        export_lights=False,
        export_cameras=False,
        export_yup=True
    )
    print(f"GLB Successfully generated at: {export_path}")

if __name__ == "__main__":
    argv = sys.argv
    is_interactive = "--" not in argv

    glb_out = r"D:\Singvox\Singvox\avatar\exports\SignVox_Female.glb"

    if is_interactive:
        print("\n[ SIGNVOX INTERACTIVE GLB EXPORTER ]")
        print("Assuming FBX is already imported via Blender UI...")
    else:
        args = argv[argv.index("--") + 1:]
        fbx_in = args[0]
        glb_out = args[1]
        
        print("\n[ SIGNVOX COMMAND-LINE GLB EXPORTER ]")
        print("WARNING: Command-line FBX import is often unstable in Blender 5.2 due to context mode_set failures.")
        if not os.path.exists(fbx_in):
            print(f"ERROR: Input FBX not found: {fbx_in}")
            sys.exit(1)
            
        print(f"Attempting to import: {fbx_in}")
        try:
            bpy.ops.import_scene.fbx(filepath=fbx_in)
        except Exception as e:
            print(f"CRITICAL FBX IMPORT FAILURE: {e}")
            print("Please fallback to interactive Blender UI import workflow!")
            sys.exit(1)

    armature, meshes, cleanup_items = find_avatar_scene()
    validate_avatar_scene(armature, meshes)
    export_glb(glb_out, cleanup_items)
