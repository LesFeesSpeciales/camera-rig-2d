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
        # camera_obj.hide_select = True
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

        corner_distance = (left_corner.head - right_corner.head).length

        center = eb.new(CENTER_NAME)
        center.head = ((right_corner.head + left_corner.head) / 2.0)
        center.tail = center.head + Vector((0.0, 0.0, BONE_LENGTH))
        center.parent = parent_bone
        # center.layers = [l==31 for l in range(32)]

        # sc.cursor_location = camera_obj.matrix_world * (camera.view_frame(sc)[1].normalized() * 10)

        bpy.ops.object.mode_set(mode='POSE')
        bones = camera_rig_object.data.bones
        pb = camera_rig_object.pose.bones

        # Bone drivers
        center_drivers = pb[CENTER_NAME].driver_add("location")

        # Center X driver
        d = center_drivers[0].driver
        d.type = 'AVERAGE'

        var = d.variables.new()
        var.name = 'left'
        var.type = 'TRANSFORMS'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = LEFT_CORNER_NAME
        var.targets[0].transform_type = 'LOC_X'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

        var = d.variables.new()
        var.name = 'right'
        var.type = 'TRANSFORMS'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = RIGHT_CORNER_NAME
        var.targets[0].transform_type = 'LOC_X'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

        # Center Y driver
        d = center_drivers[1].driver
        d.type = 'SCRIPTED'
        # d.expression = '(res_y/res_x)*dist/2 + (left + right)/2'

        d.expression = '({distance} - (left-right))*(res_y/res_x)/2'.format(distance=corner_distance)

        var = d.variables.new()
        var.name = 'left'
        var.type = 'TRANSFORMS'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = LEFT_CORNER_NAME
        var.targets[0].transform_type = 'LOC_X'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

        var = d.variables.new()
        var.name = 'right'
        var.type = 'TRANSFORMS'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = RIGHT_CORNER_NAME
        var.targets[0].transform_type = 'LOC_X'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

        var = d.variables.new()
        var.name = 'res_x'
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = sc
        var.targets[0].data_path = 'render.resolution_x'

        var = d.variables.new()
        var.name = 'res_y'
        var.type = 'SINGLE_PROP'
        var.targets[0].id_type = 'SCENE'
        var.targets[0].id = sc
        var.targets[0].data_path = 'render.resolution_y'

        # Center Z driver
        d = center_drivers[2].driver
        d.type = 'AVERAGE'

        var = d.variables.new()
        var.name = 'left'
        var.type = 'TRANSFORMS'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = LEFT_CORNER_NAME
        var.targets[0].transform_type = 'LOC_Z'
        var.targets[0].transform_space = 'TRANSFORM_SPACE'

        var = d.variables.new()
        var.name = 'right'
        var.type = 'TRANSFORMS'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = RIGHT_CORNER_NAME
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
        d = camera.driver_add('lens').driver
        d.expression = 'camera_distance *32 / frame_distance'

        var = d.variables.new()
        var.name = 'frame_distance'
        var.type = 'LOC_DIFF'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = LEFT_CORNER_NAME
        var.targets[0].transform_space = 'WORLD_SPACE'
        var.targets[1].id = camera_rig_object
        var.targets[1].bone_target = RIGHT_CORNER_NAME
        var.targets[1].transform_space = 'WORLD_SPACE'

        var = d.variables.new()
        var.name = 'camera_distance'
        var.type = 'LOC_DIFF'
        var.targets[0].id = camera_rig_object
        var.targets[0].bone_target = CENTER_NAME
        var.targets[0].transform_space = 'WORLD_SPACE'
        var.targets[1].id = camera_rig_object
        var.targets[1].bone_target = CAMERA_NAME
        var.targets[1].transform_space = 'WORLD_SPACE'


        camera_obj.parent = camera_rig_object
        camera_obj.parent_type = 'BONE'
        camera_obj.parent_bone = 'Camera'
        camera_obj.location.y = -BONE_LENGTH

        bpy.ops.object.mode_set(mode=mode)

        return {"FINISHED"}


# add entry in the Add Object > Camera Menu
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
