# region Imports
# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import IntProperty, StringProperty, CollectionProperty

# relative imports 
from . import shared
# endregion

classes = []

# region PropertyGroups
class AR_macro(shared.id_system, PropertyGroup):
    label : StringProperty()
    macro : StringProperty()
classes.append(AR_macro)

class AR_action(shared.id_system, PropertyGroup):
    label : StringProperty()
    command: CollectionProperty(type= AR_macro)
    icon : IntProperty(default= 101) #Icon BLANK1
classes.append(AR_action)
# endregion

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion