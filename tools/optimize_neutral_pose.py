import bpy
import math
import mathutils

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v3.glb")

arm = None
for obj in bpy.data.objects:
    if obj.type == 'ARMATURE':
        arm = obj
        break

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

def get_bone(name):
    for pb in arm.pose.bones:
        if name in pb.name or pb.name in name: return pb
    return arm.pose.bones[name.split(':')[-1]]

b_hips = get_bone('Hips')
b_lup_leg = get_bone('LeftUpLeg')
b_arm = get_bone('LeftArm')
b_fore = get_bone('LeftForeArm')
b_hand = get_bone('LeftHand')

def get_world_pos(pb):
    return arm.matrix_world @ pb.matrix @ pb.bone.head_local

def set_euler(pb, rot):
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2]))

# We define the ideal hand state
mat = arm.matrix_world @ b_hips.matrix
hip_world = get_world_pos(b_hips)
lup_world = get_world_pos(b_lup_leg)

# Hand should be slightly laterally outward from the leg
target_pos_x = lup_world.x + 0.12  # slightly outside hip
target_pos_y = hip_world.y          # perfectly aligned with hip depth (no forward projection!)
# Z doesn't strictly matter as much, arms just hang
target_pos_z = hip_world.z - 0.15

# 1. OPTIMIZE LEFT ARM (Elbow position)
# We want the elbow to hang down naturally beside the torso.
# Torso Y is approx hip_world.y. We want elbow to be at hip_world.y depth.
print("Optimizing LeftArm...")
best_la = (0,0,0)
best_la_dist = 9999
for la_x in range(-30, 31, 5):
    for la_y in range(-30, 31, 5):
        for la_z in range(-30, 31, 5):
            set_euler(b_arm, (la_x, la_y, la_z))
            bpy.context.view_layer.update()
            
            tail_world = arm.matrix_world @ b_arm.matrix @ b_arm.bone.tail_local
            dist_x = abs(tail_world.x - (lup_world.x + 0.15))
            dist_y = abs(tail_world.y - hip_world.y)
            dist_z = tail_world.z # want it as low as possible
            
            loss = dist_x * 10 + dist_y * 10 - dist_z 
            if loss < best_la_dist:
                best_la_dist = loss
                best_la = (la_x, la_y, la_z)

set_euler(b_arm, best_la)
bpy.context.view_layer.update()
print("Best LeftArm:", best_la)

# 2. OPTIMIZE LEFT FOREARM (Hand position and depth)
print("Optimizing LeftForeArm...")
best_lf = (0,0,0)
best_lf_dist = 9999
for lf_x in range(-90, 45, 5):
    for lf_y in range(-120, 120, 10):
        for lf_z in range(-45, 45, 5):
            set_euler(b_fore, (lf_x, lf_y, lf_z))
            bpy.context.view_layer.update()
            
            hand_world = get_world_pos(b_hand)
            dist_x = abs(hand_world.x - (lup_world.x + 0.15))
            dist_y = abs(hand_world.y - hip_world.y)
            dist_z = hand_world.z 
            
            loss = dist_x * 10 + dist_y * 20 - (dist_z * 5.0) # heavily weight keeping it down and beside hip
            if loss < best_lf_dist:
                best_lf_dist = loss
                best_lf = (lf_x, lf_y, lf_z)

set_euler(b_fore, best_lf)
bpy.context.view_layer.update()
print("Best LeftForeArm:", best_lf)

# 3. OPTIMIZE LEFT HAND (Fingers DOWN, Palm INWARD)
print("Optimizing LeftHand...")
best_lh = (0,0,0)
best_lh_dist = 9999
target_palm_dir = mathutils.Vector((-1, 0, 0)) # Pointing towards right (thigh)
target_finger_dir = mathutils.Vector((0, 0, -1)) # Pointing down

for lh_x in range(-90, 90, 5):
    for lh_y in range(-90, 90, 5):
        for lh_z in range(-90, 90, 5):
            set_euler(b_hand, (lh_x, lh_y, lh_z))
            bpy.context.view_layer.update()
            
            mat_hand = arm.matrix_world @ b_hand.matrix
            # V3 LeftHand local axes mapping:
            # We want fingers (tail-head) to point DOWN.
            fingers_dir = (mat_hand @ b_hand.bone.tail_local - get_world_pos(b_hand)).normalized()
            
            # We want palm to point towards LEFT THIGH (-X)
            # Find which local axis points palm by checking cross products or typical Mixamo mappings.
            # In Mixamo, palm normal is usually +Z or -Z.
            palm_vec1 = (mat_hand.to_3x3() @ mathutils.Vector((0, 0, 1))).normalized()
            palm_vec2 = (mat_hand.to_3x3() @ mathutils.Vector((0, 0, -1))).normalized()
            # The palm is whichever points most towards -X right now:
            
            finger_score = -fingers_dir.dot(target_finger_dir) # -1 is best
            
            # We want the palm to face -X, so we want the palm axis dot target to be max
            palm_score = min(-palm_vec1.dot(target_palm_dir), -palm_vec2.dot(target_palm_dir)) # One of these is palm
            
            loss = finger_score * 10 + palm_score * 5
            if loss < best_lh_dist:
                best_lh_dist = loss
                best_lh = (lh_x, lh_y, lh_z)

set_euler(b_hand, best_lh)
bpy.context.view_layer.update()
print("Best LeftHand:", best_lh)

best_pose = (best_la[0], best_la[1], best_la[2], best_lf[0], best_lf[1], best_lf[2], best_lh[0], best_lh[1], best_lh[2])

print("=== OPTIMIZATION DONE ===")
print("BEST POSE:", best_pose)
print("BEST LOSS:", best_loss)

# Now evaluate BEST POSE natively.
la_x, la_y, la_z, lf_x, lf_y, lf_z, lh_x, lh_y, lh_z = best_pose
set_euler(b_arm, (la_x, la_y, la_z))
set_euler(b_fore, (lf_x, lf_y, lf_z))
set_euler(b_hand, (lh_x, lh_y, lh_z))

# Ensure symmetric target natively? To save space, we just apply symmetrically (flip X/Y/Z as needed)
# Right arm:
b_r_arm = get_bone('RightArm')
b_r_fore = get_bone('RightForeArm')
b_r_hand = get_bone('RightHand')

set_euler(b_r_arm, (la_x, -la_y, -la_z))
set_euler(b_r_fore, (lf_x, -lf_y, -lf_z))
set_euler(b_r_hand, (lh_x, -lh_y, -lh_z))
bpy.context.view_layer.update()

# Final output
print("FINAL DEPTH (Y):", get_world_pos(b_hand).y, "HIP DEPTH:", hip_world.y)
print("FINAL LATERAL (X):", get_world_pos(b_hand).x, "HIP LATERAL:", hip_world.x)

