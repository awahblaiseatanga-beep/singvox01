"""Export the baked GOOD candidate .blend to a NEW pilot GLB — never production.

Mirrors Singvox/tools/export_glb.py export settings. Run headless:
    blender --background <candidate.blend> --python export_good_glb.py
(or pass paths after `--`: <candidate.blend> <out.glb>)

Reads:  Singvox/experiments/avatar/pilot_good/SignVox_GOOD_Candidate.blend (bake output)
Writes: Singvox/experiments/avatar/pilot_good/SignVox_GOOD_Candidate.glb (new file)
Never touches: web/public/avatar/*.glb, avatar/exports/*, controller, vocab, mappings.
"""
import bpy
import os
import sys

argv = sys.argv
if "--" in argv:
    args = argv[argv.index("--") + 1:]
    BLEND_IN = args[0] if len(args) > 0 else None
    GLB_OUT = args[1] if len(args) > 1 else None
else:
    BLEND_IN = None
    GLB_OUT = None

_HERE = os.path.dirname(os.path.abspath(__file__))
if not BLEND_IN:
    BLEND_IN = os.path.join(_HERE, "SignVox_GOOD_Candidate.blend")
if not GLB_OUT:
    GLB_OUT = os.path.join(_HERE, "SignVox_GOOD_Candidate.glb")

if not os.path.exists(BLEND_IN):
    print(f"ERROR: Candidate .blend not found: {BLEND_IN}", file=sys.stderr)
    sys.exit(1)

bpy.ops.wm.open_mainfile(filepath=BLEND_IN)

# Remove cameras/lights so the candidate matches production export hygiene.
for obj in [o for o in bpy.context.scene.objects if o.type in ('CAMERA', 'LIGHT')]:
    bpy.data.objects.remove(obj, do_unlink=True)

arm = next((o for o in bpy.context.scene.objects if o.type == 'ARMATURE'), None)
if not arm:
    print("ERROR: No armature in candidate .blend", file=sys.stderr)
    sys.exit(1)

names = [a.name for a in bpy.data.actions]
print(f"Actions in candidate: {names}")
if "ASL_GOOD" not in names:
    print("ERROR: ASL_GOOD action missing from candidate .blend", file=sys.stderr)
    sys.exit(1)

os.makedirs(os.path.dirname(GLB_OUT), exist_ok=True)
bpy.ops.export_scene.gltf(
    filepath=GLB_OUT,
    export_format='GLB',
    use_selection=False,
    export_apply=True,
    export_animations=True,
    export_skins=True,
    export_morph=True,
    export_materials='EXPORT',
    export_lights=False,
    export_cameras=False,
    export_yup=True,
)
print(f"GOOD CANDIDATE GLB exported: {GLB_OUT}")
