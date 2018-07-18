# Copyright (C) 2018 Les Fees Speciales
# voeu@les-fees-speciales.coop
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


bl_info = {
    "name": "2D Camera Rig",
    "author": "Les Fees Speciales",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "View3D > Add > Camera > 2D Camera Rig",
    "description": "Create a camera rig suiting 2D content",
    "category": "Camera"
}

import bpy
from mathutils import Vector
from math import cos, sin, pi
from rna_prop_ui import rna_idprop_ui_prop_get

def create_corner_shape(name, reverse=False):
    mesh = bpy.data.meshes.new('WGT-'+name)
    obj = bpy.data.objects.new('WGT-'+name, mesh)
    reverse = -1 if reverse else 1
    verts = (Vector((reverse *  0.0, 0.0, 0.0)),
             Vector((reverse *  0.0, 1.0, 0.0)),
             Vector((reverse * -0.1, 1.0, 0.0)),
             Vector((reverse * -0.1, 0.1, 0.0)),
             Vector((reverse * -1.0, 0.1, 0.0)),
             Vector((reverse * -1.0, 0.0, 0.0)),
             )
    edges = [(n, (n+1) % len(verts)) for n in range(len(verts))]
    mesh.from_pydata(verts, edges, ())
    return obj


def create_circle_shape(name):
    mesh = bpy.data.meshes.new('WGT-'+name)
    obj = bpy.data.objects.new('WGT-'+name, mesh)
    verts = []
    vert_n = 16
    for n in range(vert_n):
        angle = n/vert_n*2*pi
        verts.append(Vector((cos(angle), sin(angle), 0.0)))
    edges = [(n, (n+1) % len(verts)) for n in range(len(verts))]
    mesh.from_pydata(verts, edges, ())
    return obj


class Create2DCameraRig(bpy.types.Operator):
    bl_idname = "object.camera_rig_2d_create"
    bl_label = "Create 2D Camera Rig"
    bl_description = "Create a camera rig suiting 2D content"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        sc = bpy.context.scene
        mode = bpy.context.mode

        BONE_LENGTH = 0.5
        PARENT_NAME = 'Parent'
        CAMERA_NAME = 'Camera'
        LEFT_CORNER_NAME = 'Left Corner'
        RIGHT_CORNER_NAME = 'Right Corner'
        CENTER_NAME = 'Center'

        # Create camera
        camera = bpy.data.cameras.new(CAMERA_NAME)
        camera.lens = 170.0
        camera_obj = bpy.data.objects.new(CAMERA_NAME, camera)
        sc.objects.link(camera_obj)

        # Create armature
        camera_rig = bpy.data.armatures.new('Camera Rig')
        camera_rig_object = bpy.data.objects.new('Camera Rig', camera_rig)
        sc.objects.link(camera_rig_object)
        camera_rig_object.location = sc.cursor_location

        sc.objects.active = camera_rig_object

        bpy.ops.object.mode_set(mode='EDIT')
        eb = camera_rig.edit_bones
        parent_bone = eb.new(PARENT_NAME)
        parent_bone.tail = Vector((0.0, 0.0, BONE_LENGTH))

        camera_bone = eb.new('Camera')
        camera_bone.tail = Vector((0.0, 0.0, BONE_LENGTH))
        camera_bone.parent = parent_bone

        corners = camera.view_frame(sc)[1:3]

        left_corner = eb.new(LEFT_CORNER_NAME)
        left_corner.head = parent_bone.matrix * corners[1] * 100
        left_corner.tail = left_corner.head + Vector((0.0, 0.0, BONE_LENGTH))
        left_corner.parent = parent_bone

        right_corner = eb.new(RIGHT_CORNER_NAME)
        right_corner.head = parent_bone.matrix * corners[0] * 100
        right_corner.tail = right_corner.head + Vector((0.0, 0.0, BONE_LENGTH))
        right_corner.parent = parent_bone

        corner_distance_x = (left_corner.head - right_corner.head).length
        corner_distance_y = -left_corner.head.z
        corner_distance_z = left_corner.head.y

        center = eb.new(CENTER_NAME)
        center.head = ((right_corner.head + left_corner.head) / 2.0)
        center.tail = center.head + Vector((0.0, 0.0, BONE_LENGTH))
        center.parent = parent_bone
        center.layers = [layer == 31 for layer in range(32)]

        bpy.ops.object.mode_set(mode='POSE')
        bones = camera_rig_object.data.bones
        pb = camera_rig_object.pose.bones

        # Bone drivers
        center_drivers = pb[CENTER_NAME].driver_add("location")

        # Center X driver
        d = center_drivers[0].driver
        d.type = 'AVERAGE'

        for corner in ('left', 'right'):
            var = d.variables.new()
            var.name = corner
            var.type = 'TRANSFORMS'
            var.targets[0].id = camera_rig_object
            var.targets[0].bone_target = corner.capitalize() + ' Corner'
            var.targets[0].transform_type = 'LOC_X'
            var.targets[0].transform_space = 'TRANSFORM_SPACE'

        # Center Y driver
        d = center_drivers[1].driver
        d.type = 'SCRIPTED'

        d.expression = '({distance_x} - (left_x-right_x))*(res_y/res_x)/2 + (left_y + right_y)/2'.format(distance_x=corner_distance_x)

        for direction in ('x', 'y'):
            for corner in ('left', 'right'):
                var = d.variables.new()
                var.name = '%s_%s' % (corner, direction)
                var.type = 'TRANSFORMS'
                var.targets[0].id = camera_rig_object
                var.targets[0].bone_target = corner.capitalize() + ' Corner'
                var.targets[0].transform_type = 'LOC_' + direction.upper()
                var.targets[0].transform_space = 'TRANSFORM_SPACE'

            var = d.variables.new()
            var.name = 'res_' + direction
            var.type = 'SINGLE_PROP'
            var.targets[0].id_type = 'SCENE'
            var.targets[0].id = sc
            var.targets[0].data_path = 'render.resolution_' + direction

        # Center Z driver
        d = center_drivers[2].driver
        d.type = 'AVERAGE'

        for corner in ('left', 'right'):
            var = d.variables.new()
            var.name = corner
            var.type = 'TRANSFORMS'
            var.targets[0].id = camera_rig_object
            var.targets[0].bone_target = corner.capitalize() + ' Corner'
            var.targets[0].transform_type = 'LOC_Z'
            var.targets[0].transform_space = 'TRANSFORM_SPACE'

        # Bone constraints
        con = pb[CAMERA_NAME].constraints.new('DAMPED_TRACK')
        con.target = camera_rig_object
        con.subtarget = CENTER_NAME
        con.track_axis = 'TRACK_NEGATIVE_Z'


        # Bone Display
        left_shape = create_corner_shape(LEFT_CORNER_NAME, reverse=True)
        bones[LEFT_CORNER_NAME].show_wire = True
        pb[LEFT_CORNER_NAME].custom_shape = left_shape

        right_shape = create_corner_shape(RIGHT_CORNER_NAME)
        bones[RIGHT_CORNER_NAME].show_wire = True
        pb[RIGHT_CORNER_NAME].custom_shape = right_shape

        parent_shape = create_circle_shape(PARENT_NAME)
        bones[PARENT_NAME].show_wire = True
        pb[PARENT_NAME].custom_shape = parent_shape

        camera_shape = create_circle_shape(CAMERA_NAME)
        bones[CAMERA_NAME].show_wire = True
        pb[CAMERA_NAME].custom_shape = camera_shape
        pb[CAMERA_NAME].custom_shape_scale = 0.7

        # Bone transforms
        pb[LEFT_CORNER_NAME].rotation_mode = 'XYZ'
        pb[LEFT_CORNER_NAME].lock_rotation = (True,) * 3

        pb[RIGHT_CORNER_NAME].rotation_mode = 'XYZ'
        pb[RIGHT_CORNER_NAME].lock_rotation = (True,) * 3

        pb[PARENT_NAME].rotation_mode = 'XYZ'

        pb[CAMERA_NAME].rotation_mode = 'XYZ'
        pb[CAMERA_NAME].lock_location = (False, False, True)
        pb[CAMERA_NAME].lock_rotation = (True,) * 3
        pb[CAMERA_NAME].lock_scale = (True,) * 3

        # Camera settings
        camera_rig_object['rotation_shift'] = 0.0
        prop = rna_idprop_ui_prop_get(camera_rig_object, 'rotation_shift', create=True)

        prop["min"] = 0.0
        prop["max"] = 1.0
        prop["soft_min"] = 0.0
        prop["soft_max"] = 1.0
        prop["description"] = 'rotation_shift'

        # Rotation / shift switch
        d = con.driver_add('influence').driver
        d.expression = '1 - rotation_shift'

        var = d.variables.new()
        var.name = 'rotation_shift'
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = camera_rig_object
        var.targets[0].data_path = '["rotation_shift"]'

        # Focal length driver
        d = camera.driver_add('lens').driver
        d.expression = 'abs({distance_z} - (left_z + right_z)/2) * 32 / frame_width'.format(distance_z=corner_distance_z)

        var = d.variables.new()
        var.name = 'frame_width'
        var.type = 'LOC_DIFF'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = LEFT_CORNER_NAME
        var.targets[0].transform_space = 'WORLD_SPACE'
        var.targets[1].id = camera_rig_object
        var.targets[1].bone_target = RIGHT_CORNER_NAME
        var.targets[1].transform_space = 'WORLD_SPACE'

        for corner in ('left', 'right'):
            var = d.variables.new()
            var.name = corner + '_z'
            var.type = 'TRANSFORMS'
            var.targets[0].id = camera_rig_object
            var.targets[0].bone_target = corner.capitalize() + ' Corner'
            var.targets[0].transform_type = 'LOC_Z'
            var.targets[0].transform_space = 'TRANSFORM_SPACE'

        # Orthographic scale driver
        d = camera.driver_add('ortho_scale').driver
        d.expression = 'abs({distance_x} - (left_x - right_x))'.format(distance_x=corner_distance_x)

        for corner in ('left', 'right'):
            var = d.variables.new()
            var.name = corner + '_x'
            var.type = 'TRANSFORMS'
            var.targets[0].id = camera_rig_object
            var.targets[0].bone_target = corner.capitalize() + ' Corner'
            var.targets[0].transform_type = 'LOC_X'
            var.targets[0].transform_space = 'TRANSFORM_SPACE'


        # Shift driver X
        d = camera.driver_add('shift_x').driver

        d.expression = 'rotation_shift * (((left_x + right_x)/2 - cam_x) * lens / abs({distance_z} - (left_z + right_z)/2) / sensor_width)'.format(distance_z=corner_distance_z)

        var = d.variables.new()
        var.name = 'rotation_shift'
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = camera_rig_object
        var.targets[0].data_path = '["rotation_shift"]'

        for direction in ('x', 'z'):
            for corner in ('left', 'right'):
                var = d.variables.new()
                var.name = '%s_%s' % (corner, direction)
                var.type = 'TRANSFORMS'
                var.targets[0].id = camera_rig_object
                var.targets[0].bone_target = corner.capitalize() + ' Corner'
                var.targets[0].transform_type = 'LOC_' + direction.upper()
                var.targets[0].transform_space = 'TRANSFORM_SPACE'

        var = d.variables.new()
        var.name = 'cam_x'
        var.type = 'TRANSFORMS'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = CAMERA_NAME
        var.targets[0].transform_type = 'LOC_X'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

        var = d.variables.new()
        var.name = 'lens'
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'CAMERA'
        var.targets[0].id = camera
        var.targets[0].data_path = 'lens'

        var = d.variables.new()
        var.name = 'sensor_width'
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'CAMERA'
        var.targets[0].id = camera
        var.targets[0].data_path = 'sensor_width'

        # Shift driver Y
        d = camera.driver_add('shift_y').driver

        d.expression = 'rotation_shift * -(({distance_y} - (left_y + right_y)/2 - cam_y) * lens / abs({distance_z} - (left_z + right_z)/2) / sensor_width - (res_y/res_x)/2)'.format(distance_y=corner_distance_y, distance_z=corner_distance_z)

        var = d.variables.new()
        var.name = 'rotation_shift'
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = camera_rig_object
        var.targets[0].data_path = '["rotation_shift"]'

        for direction in ('y', 'z'):
            for corner in ('left', 'right'):
                var = d.variables.new()
                var.name = '%s_%s' % (corner, direction)
                var.type = 'TRANSFORMS'
                var.targets[0].id = camera_rig_object
                var.targets[0].bone_target = corner.capitalize() + ' Corner'
                var.targets[0].transform_type = 'LOC_' + direction.upper()
                var.targets[0].transform_space = 'TRANSFORM_SPACE'

        for direction in ('x', 'y'):
            var = d.variables.new()
            var.name = 'res_' + direction
            var.type = 'SINGLE_PROP'
            var.targets[0].id_type = 'SCENE'
            var.targets[0].id = sc
            var.targets[0].data_path = 'render.resolution_' + direction

        var = d.variables.new()
        var.name = 'cam_y'
        var.type = 'TRANSFORMS'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = CAMERA_NAME
        var.targets[0].transform_type = 'LOC_Y'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

        var = d.variables.new()
        var.name = 'lens'
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'CAMERA'
        var.targets[0].id = camera
        var.targets[0].data_path = 'lens'

        var = d.variables.new()
        var.name = 'sensor_width'
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'CAMERA'
        var.targets[0].id = camera
        var.targets[0].data_path = 'sensor_width'

        # Parent camera object to rig
        camera_obj.parent = camera_rig_object
        camera_obj.parent_type = 'BONE'
        camera_obj.parent_bone = 'Camera'
        camera_obj.location.y = -BONE_LENGTH
        camera_obj.lock_location = (True,) * 3
        camera_obj.lock_rotation = (True,) * 3
        camera_obj.lock_scale = (True,) * 3

        bpy.ops.object.mode_set(mode=mode)

        return {"FINISHED"}


# Add entry in the Add Object > Camera Menu
def add_2d_rig_buttons(self, context):
    if context.mode == 'OBJECT':
        self.layout.operator(
                    Create2DCameraRig.bl_idname,
                    text="2D Camera Rig",
                    icon='CAMERA_DATA'
                    )


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_camera_add.append(add_2d_rig_buttons)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_camera_add.remove(add_2d_rig_buttons)


if __name__ == "__main__":
    register()
