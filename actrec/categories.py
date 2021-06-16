# region Imports
# external modules
import json
import os
from collections import defaultdict
from contextlib import suppress

# blender modules
import bpy
from bpy.types import Operator, PropertyGroup, Panel
from bpy.props import StringProperty, EnumProperty, IntProperty, CollectionProperty, BoolProperty, StringProperty

# relativ imports
from .preferences import AR_preferences
from . import globals, log, shared
# endregion 

classes = []

# region PropertyGroups
# endregion

# region preferences
class preferences:

    AR = bpy.context.preferences.addons[__package__].preferences
    category_visibility_path = os.path.join(AR.exact_storage_path, "Category_Visibility") # set the category visibility path
# endregion

# region Registration 
def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
# endregion 
