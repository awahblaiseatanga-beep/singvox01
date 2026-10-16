import bpy

bpy.ops.wm.read_homefile(filepath=r"d:\Singvox\Singvox\avatar\exports\SignVox_HELLO_BlendRepair.blend")

# 1. Clean up the massive black relationship lines and previous V3 markers securely
junk = ["Icosphere", "Cube", "Chest_Target", "LeftHip", "RightHip", "Hand_Target", "MP_Trace", "Plane", "T_Elb", "T_Wri", "T_"]
for obj in list(bpy.data.objects):
    if any(j in obj.name.replace("_", "") for j in junk) or obj.name.startswith("Cube"):
        try: bpy.data.objects.remove(obj, do_unlink=True)
        except: pass

arm = bpy.data.objects.get("Armature")
bpy.context.view_layer.objects.active = arm

bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.transforms_clear()

act = bpy.data.actions.get("ASL_HELLO")
if act: bpy.data.actions.remove(act)
new_act = bpy.data.actions.new("ASL_HELLO")
if not arm.animation_data: arm.animation_data_create()
arm.animation_data.action = new_act

# 2. Extract Head coordinate to relative spatial offset mappings
head = arm.pose.bones["mixamorig4:Head"].head
# Base Mixamo origin typically 0,0,0
hx, hy, hz = head.x, head.y, head.z 

def make_target(name):
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    e = bpy.context.active_object
    e.name = name
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    return e

t_hand = make_target("T_Hand_IK")
t_pole = make_target("T_Pole_IK")

# Lock pole strictly outwards/back to force elbow outward natively
t_pole.location = (hx + 0.8, hy + 0.5, hz - 0.2)

# Constraint mapping
b_hand = arm.pose.bones["mixamorig4:RightHand"]
c_ik = b_hand.constraints.new('IK')
c_ik.target = t_hand
c_ik.pole_target = t_pole
c_ik.pole_angle = -1.57 # Mixamo generic pole lock
c_ik.chain_count = 2

# Map ASL_HELLO spatial points (Z is Up, -Y is Forward, +X is Right)
p_rest = (hx + 0.3, hy, hz - 0.7)
p_head = (hx + 0.2, hy - 0.2, hz - 0.1) # Right temple
p_ext = (hx + 0.4, hy - 0.5, hz - 0.2) # Extended forward/outward

t_hand.location = p_rest
t_hand.keyframe_insert(data_path="location", frame=0)

t_hand.location = p_head
t_hand.keyframe_insert(data_path="location", frame=12)

t_hand.location = p_ext
t_hand.keyframe_insert(data_path="location", frame=22)

t_hand.location = p_rest
t_hand.keyframe_insert(data_path="location", frame=35)

# Bake explicit rigid limits removing constraints safely
bpy.ops.nla.bake(
    frame_start=0, frame_end=40,
    only_selected=False, visual_keying=True,
    clear_constraints=True, use_current_action=True, bake_types={'POSE'}
)

if "ASL_HELLO" in arm.animation_data.nla_tracks:
    arm.animation_data.nla_tracks.remove(arm.animation_data.nla_tracks["ASL_HELLO"])

track = arm.animation_data.nla_tracks.new()
track.name = "ASL_HELLO"
track.strips.new("HELLO", 0, new_act)

bpy.ops.object.mode_set(mode='OBJECT')
bpy.data.objects.remove(t_hand, do_unlink=True)
bpy.data.objects.remove(t_pole, do_unlink=True)

# Export validation state!
bpy.ops.wm.save_as_mainfile(filepath=r"d:\Singvox\Singvox\avatar\exports\SignVox_HELLO_BlendRepair.blend")
print("V5 BLOCKOUT GENERATED")
