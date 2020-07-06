## Deprecation
This project is now [included with Blender](https://docs.blender.org/manual/en/latest/addons/camera/camera_rigs.html).

-----

# Camera Rig 2D
Create a 2D camera rig well suited for cutout animation

### Usage
Add the rig through the Add Menu (`SHIFT` + `A`) > Camera > 2D Camera Rig.
This creates a camera parented to an armature. There are two controllers for
the camera, one for each bottom corner. Camera rotation or shift and focal length
are calculated automatically.

You may choose between two modes, located in the Camera Rig Custom
Properties:
* Rotation: this rotates the camera to keep controllers in the corners of
the field of view. Perspective deformations will appear when the controllers
are sideways from the camera.
* Shift: this uses the *shift* property of the camera object. In perspective mode,
this incurs another type of deformation at extreme angles.

You may find an article explaining the add-on in further detail [here](http://lacuisine.tech/2018/07/19/2d-camera-rig/).

### Known issues
* Rotation mode is unsupported for orthographic cameras.

-----

## License

Blender scripts shared by **Les Fées Spéciales** are, except where
otherwise noted, licensed under the GPLv2 license.
