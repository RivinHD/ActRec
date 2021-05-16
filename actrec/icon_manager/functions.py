# region Imports
# external modules
from typing import Optional
import os

# blender modules
import bpy

# relative imports
from ..preferences import AR_preferences
# endregion

# region functions

def get_icons_values():
    return [icon.value for icon in bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.values()[1:]]

def get_icons():
    return bpy.types.UILayout.bl_rna.functions["prop"].parameters["icon"].enum_items.keys()[1:]

def load_icons(filepath: str, only_new: bool = False) -> Optional[str]:
    img = bpy.data.images.load(filepath)
    if img.size[0] == img.size[1]:
        AR_Var = bpy.context.preferences.addons[__package__].preferences
        img.scale(32, 32)
        split = img.name.split('.') # last element is format of file
        img.name = '.'.join(split[:-1])
        internalpath = os.path.join(AR_Var.IconFilePath, img.name + "." + split[-1])
        img.save_render(internalpath)
        register_icon(AR_preferences.preview_collections['ar_custom'], "AR_" + img.name, internalpath, only_new)
        bpy.data.images.remove(img)
    else:
        bpy.data.images.remove(img)
        return 'The Image must be a square'

def register_icon(pcoll, name: str, filepath: str, only_new: bool):
    try:
        if only_new and not(name in pcoll):
            pcoll.load(name, filepath, 'IMAGE', force_reload= True)
    except:
        split = name.split('.')
        if len(split) > 1 and split[-1].isnumeric():
            name = ".".join(split[:-1]) + str(int(split[-1]) + 1)
        else:
            name = name + ".1"
        register_icon(pcoll, name, filepath)

def unregister_icon(pcoll, name: str):
    del pcoll[name]
#endregion
