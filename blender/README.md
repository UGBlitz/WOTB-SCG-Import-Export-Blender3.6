# io\_scene\_dava
Blender addon to read Scene Graph (.scg) format used by the DAVA game engine to store raw 3d geometry.

## Status
Can import and export existing scg files properly to be used in game

## Install
The addon requires, blender 3.6.

1. Download [io_scene_dava_1_7_0.zip](https://github.com/UGBlitz/WOTB-SCG-Import-Export-Blender3.6/releases/tag/1.7.0), and extract it
2. Install the addon, copy the `io_scene_dava` folder to your blender `addons` folder.
4. Enable the addon, in blender go to `Edit > Preferences > Add-ons` and search for `DAVA` and enable the plugin.
3. Use the addon, see `Status` on this page for available features.

## Tutorial and Features
### Importing
Import a file: `File > Import > DAVA Scene`. The plugin imports all objects in the scg, thus it imports all lods of the visual model and also imports locators and attachment sockets (small triangles used by DAVA). I recommend not touching any of the locators or the tracks since i havent tried editing them. You have to figure out which objcect is of what lod by seeing the vertex counts and trial an error (like moving an object to see if something moves in game).


### UV
The plugin can import UVS properly and UVS of any object can be edited through blender's UV Editing tab

### Modifying Existing Objects
Any existing object can be modifed with blender's edit mode, before export all modifiers and transforms need to be applied. You cannot remove an object entirely, but you can collapse an object into a single point. Objects can be renamed without any issue but you cannot use underscores as those reserved for another function explained below.

### Adding New Geometry
You can import/make a new mesh object and name it in the manner `<name of parent>_<name of your choice>` here 
`<name of parent>` must refer to an object in the original scg, for example if you want to add a sphere which rotates with the turret, you find the lod0 turret (if you want the sphere to appear only when the player is nearby or else you can add it on all lod turrets) from the mess and say rename it to `turret01LOD0` (if you want), then you add your sphere and name it `turret01LOD0_sphere`. Both parts before and after the underscore in the new objects name should not have any underscores. A new object cannot be made without parenting (naming logic) it to an object that was in the original scg.

### Exporting
Export a file: `File > Export > DAVA Scene`. Make sure that no original objects of the scg were deleted/entirely removed and any new object is named properly. Before export remember to apply all modifiers and transforms for all/edited/new objects. As scgs only contain 3d geometry you cannot add any animations/other stuff.
