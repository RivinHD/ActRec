# region Imports
# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, StringProperty, IntProperty

# relative Imports
from . import shared
# endregion

# region PropertyGroups
class AR_local_actions(shared.AR_action, PropertyGroup):
    def get_selected_macro_index(self):
        value = self.get('selected_macro_index', 0)
        commands_length = len(self.macros)
        return value if value < commands_length else commands_length - 1
    def set_selected_macro_index(self, value):
        commands_length = len(self.macros)
        self['selected_macro_index'] = value if value < commands_length else commands_length - 1

    selected_macro_index : IntProperty(min= 0, get= get_selected_macro_index, set= set_selected_macro_index)

class AR_local_load_text(PropertyGroup):
    name : StringProperty()
    apply : BoolProperty(default= False)
# endregion

classes = [
    AR_local_actions,
    AR_local_load_text
]

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion