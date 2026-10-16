import bpy

bpy.ops.wm.read_homefile(filepath=r"d:\Singvox\Singvox\avatar\exports\SignVox_HELLO_BlendRepair.blend")
arm = bpy.data.objects.get("Armature")

act = bpy.data.actions.get("ASL_HELLO")
if act: bpy.data.actions.remove(act)
new_act = bpy.data.actions.new("ASL_HELLO")
if not arm.animation_data:
    arm.animation_data_create()
arm.animation_data.action = new_act

for b in arm.pose.bones: 
    b.rotation_mode = 'XYZ'
    b.keyframe_insert(data_path="rotation_euler", frame=0)

def set_rot(bname, xyz, frame):
    bone = arm.pose.bones.get(bname)
    bone.rotation_euler = xyz
    bone.keyframe_insert(data_path="rotation_euler", frame=frame)

# Frame 0: Neutral (Arms fully down by sides)
set_rot("mixamorig4:LeftArm", (0, 0, -1.4), 0)
set_rot("mixamorig4:LeftForeArm", (0, 0, 0), 0)
set_rot("mixamorig4:RightArm", (0, 0, 1.4), 0)
set_rot("mixamorig4:RightForeArm", (0, 0, 0), 0)
set_rot("mixamorig4:RightHand", (0, 0, 0), 0)

# Frame 12: Salute Peak (Head/Temple explicit)
set_rot("mixamorig4:LeftArm", (0, 0, -1.4), 12)
set_rot("mixamorig4:LeftForeArm", (0, 0, 0), 12)
# Z = High elevation, Y = forward
set_rot("mixamorig4:RightArm", (0, 0.6, -1.2), 12) # Lift significantly higher toward head
set_rot("mixamorig4:RightForeArm", (0, 0, -2.2), 12) # Maximum bend to touch temple
set_rot("mixamorig4:RightHand", (0.3, -0.3, 0.5), 12) # Align palm flush to head

# Frame 22: Flipped forward (The away snap)
set_rot("mixamorig4:LeftArm", (0, 0, -1.4), 22)
set_rot("mixamorig4:LeftForeArm", (0, 0, 0), 22)
set_rot("mixamorig4:RightArm", (0, 0.5, -0.5), 22) # Pointing forward and outward smoothly
set_rot("mixamorig4:RightForeArm", (0, 0, -0.3), 22) # Soft unbend
set_rot("mixamorig4:RightHand", (0.5, 0, 0), 22) 

# Frame 35: Neutral Default Drop
set_rot("mixamorig4:LeftArm", (0, 0, -1.4), 35)
set_rot("mixamorig4:LeftForeArm", (0, 0, 0), 35)
set_rot("mixamorig4:RightArm", (0, 0, 1.4), 35)
set_rot("mixamorig4:RightForeArm", (0, 0, 0), 35)
set_rot("mixamorig4:RightHand", (0, 0, 0), 35)

if "ASL_HELLO" in arm.animation_data.nla_tracks:
    arm.animation_data.nla_tracks.remove(arm.animation_data.nla_tracks["ASL_HELLO"])

track = arm.animation_data.nla_tracks.new()
track.name = "ASL_HELLO"
track.strips.new("HELLO", 0, new_act)

import logging
logging.getLogger("glTF-Blender-IO").setLevel(logging.CRITICAL)
bpy.ops.export_scene.gltf(
    filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v5_HELLO.glb",
    export_format='GLB',
    use_selection=False,
    export_animations=True,
    export_rest_position_armature=False,
    export_apply=True
)

bpy.ops.wm.save_as_mainfile(filepath=r"d:\Singvox\Singvox\avatar\exports\SignVox_HELLO_BlendRepair.blend")
print("MANUAL V5 EXTRACTED AND EXPORTED")
