# region Imports
# blender modules
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, StringProperty

# relative Imports
from . import shared
# endregion

classes = []

class AR_local_actions(shared.AR_action, PropertyGroup):
    pass
classes.append(AR_local_actions)

class AR_local_load_text(PropertyGroup):
    name : StringProperty()
    apply : BoolProperty(default= False)
classes.append(AR_local_load_text)