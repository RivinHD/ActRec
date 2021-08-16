# region Imports
# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty
# endregion

class AR_macro_multiline(PropertyGroup):
    text : StringProperty()

classes = [
    AR_macro_multiline
]

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion