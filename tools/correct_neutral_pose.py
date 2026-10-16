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

# Clear old pose
for pb in arm.pose.bones:
    pb.matrix_basis = mathutils.Matrix.Identity(4)
    pb.rotation_mode = 'QUATERNION'

neutral_action = bpy.data.actions.new(name="ASL_NEUTRAL")
if not arm.animation_data:
    arm.animation_data_create()
arm.animation_data.action = neutral_action

def get_bone(name):
    for pb in arm.pose.bones:
        if name in pb.name or pb.name in name: return pb
    return arm.pose.bones[name.split(':')[-1]]

def apply_direction(bone_name, track_dir, up_dir=None):
    pb = get_bone(bone_name)
    
    # Create target empty for primary Damped Track
    target = bpy.data.objects.new("Target", None)
    bpy.context.collection.objects.link(target)
    
    # Calculate track axis dynamically by finding local longitudinal axis
    head = pb.bone.head_local
    tail = pb.bone.tail_local
    local_vec = (tail - head).normalized()
    track_axis = 'TRACK_Y'
    if abs(local_vec.x) > 0.9: track_axis = 'TRACK_X' if local_vec.x > 0 else 'TRACK_NEGATIVE_X'
    elif abs(local_vec.z) > 0.9: track_axis = 'TRACK_Z' if local_vec.z > 0 else 'TRACK_NEGATIVE_Z'
    else: track_axis = 'TRACK_Y' if local_vec.y > 0 else 'TRACK_NEGATIVE_Y'
    
    # Set target location
    mat_world = arm.matrix_world @ pb.matrix
    head_world = mat_world @ pb.bone.head_local
    target.location = head_world + mathutils.Vector(track_dir) * 5
    
    con = pb.constraints.new('DAMPED_TRACK')
    con.target = target
    con.track_axis = track_axis
    
    up_target = None
    con2 = None
    if up_dir:
        up_target = bpy.data.objects.new("UpTarget", None)
        bpy.context.collection.objects.link(up_target)
        up_target.location = head_world + mathutils.Vector(up_dir) * 5
        
        con2 = pb.constraints.new('LOCKED_TRACK')
        con2.target = up_target
        con2.track_axis = 'TRACK_Z' # Default palm or front axis 
        # Actually it's safer to just let Damped Track point, and we can apply Roll manually later if needed.
        # But let's try Locked Track X to align twist!
        con2.locked_axis = track_axis
        con2.track_axis = 'TRACK_X' # Assuming X points forward/back for arm?
        
    bpy.context.view_layer.update()
    
    final_mat = pb.matrix.copy()
    pb.constraints.remove(con)
    if up_target: pb.constraints.remove(con2)
    
    pb.matrix = final_mat
    pb.keyframe_insert(data_path="rotation_quaternion", frame=0)
    
    bpy.data.objects.remove(target)
    if up_target:
        bpy.data.objects.remove(up_target)
        
    bpy.context.view_layer.update()

# Natural Standing limits:
# 1. LeftArm (Shoulder to Elbow) -> points down and slightly outward (0.1, 0, -1)
# 2. RightArm -> points down and slightly outward (-0.1, 0, -1)
# 3. LeftForeArm -> points down (0, 0, -1)
# 4. RightForeArm -> points down (0, 0, -1)
apply_direction('LeftArm', (0.15, 0, -0.9))
apply_direction('RightArm', (-0.15, 0, -0.9))

apply_direction('LeftForeArm', (0.1, 0, -0.95))
apply_direction('RightForeArm', (-0.1, 0, -0.95))

# Hands point generally down
apply_direction('LeftHand', (0.05, 0, -1))
apply_direction('RightHand', (-0.05, 0, -1))

# Now we need to ensure the palms are facing inwards.
# The mathematical transform above applied the minimum rotation to reach the downward target.
# If they are twisted outwards, we can twist them smoothly.
# I will output renders immediately so we can verify!

bpy.ops.object.mode_set(mode='OBJECT')
bpy.context.view_layer.update()

# Render Setup
camera_data = bpy.data.cameras.new(name='Camera')
camera_object = bpy.data.objects.new('Camera', camera_data)
bpy.context.collection.objects.link(camera_object)
bpy.context.scene.camera = camera_object

light_data = bpy.data.lights.new(name='Light', type='SUN')
light_data.energy = 5
light_obj = bpy.data.objects.new(name='Light', object_data=light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.location = (0, -2, 3)

bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800
bpy.context.scene.render.image_settings.file_format = 'PNG'

# Render Front
camera_object.location = (0, -2.5, 1.0) 
camera_object.rotation_euler = (math.radians(85), 0, 0)
bpy.context.scene.render.filepath = r"C:\Users\PC\.gemini\antigravity\brain\ad0cf972-41cc-42d5-893d-2b8831a21d55\neutral_front_v5.png"
bpy.ops.render.render(write_still=True)

# Render Side
camera_object.location = (2.5, 0, 1.0) 
camera_object.rotation_euler = (math.radians(85), 0, math.radians(90))
bpy.context.scene.render.filepath = r"C:\Users\PC\.gemini\antigravity\brain\ad0cf972-41cc-42d5-893d-2b8831a21d55\neutral_side_v5.png"
bpy.ops.render.render(write_still=True)

print("Visuals rendered successfully")

export_path = r"d:\Singvox\Singvox\web\public\avatar\SignVox_Female_v5_Neutral.glb"
bpy.ops.export_scene.gltf(
    filepath=export_path,
    export_format='GLB',
    use_selection=False,
    export_materials='EXPORT',
    export_animations=True,
    export_current_frame=True,
    export_animation_mode='ACTIONS',
    export_yup=True
)

print(f"Exported to {export_path}")
