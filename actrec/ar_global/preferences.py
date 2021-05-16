# region Imports
# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, IntProperty, CollectionProperty

# relative imports
from .. import preferences
# endregion

classes = []

# region PropertyGroups
class AR_global_actions_enum(PropertyGroup):
    def get_value(self) -> bool:
        return self.get("selected", False)
    def set_value(self, value: bool) -> None:
        AR = bpy.context.preferences.addons[__package__].preferences
        selected_indexes = AR.get("global_actions_enum.selected_indexes", [])
        if value:
            ctrl_value = bpy.ops.ar.check_ctrl('INVOKE_DEFAULT')
            if selected_indexes != [] and ctrl_value == 'CANCELLED':
                for selected_index in selected_indexes:
                    AR.global_actions_enum[selected_index] = False
                AR["global_actions_enum.selected_indexes"].clear()
            AR["global_actions_enum.selected_indexes"].append(self.index)
            self['selected'] = value
        elif not (self.index in selected_indexes):
            self['selected'] = value

    selected : BoolProperty(default= False, set= set_value, get= get_value, description= "Select this Action Button", name = 'Select')
    index : IntProperty()
classes.append(AR_global_actions_enum)
# endregion

# region preferences
class Preferences:
    AR = bpy.context.preferences.addons[__package__].preferences
    AR.setdefault("global_actions_enum.selected_indexes", [])

    global_actions : CollectionProperty(type= preferences.AR_action)
    global_actions_selections = AR["global_actions_enum.selected_indexes"]
    global_actions_enum : CollectionProperty(type= AR_global_actions_enum)
# endregiom

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion
