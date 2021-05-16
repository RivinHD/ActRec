# region Imports
# blender modules
import bpy
# endregion


# region functions
def check_for_dublicates(l, name, num = 1): #Check for name dublicates and append .001, .002 etc.
    if name in l:
        return check_for_dublicates(l, name.split(".")[0] +".{0:03d}".format(num), num + 1)
    return name

# endregion