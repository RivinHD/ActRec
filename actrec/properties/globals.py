# region Imports
# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, IntProperty
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
                AR["global_actions_enum.selected_indexes"].clear()
                for selected_index in selected_indexes:
                    AR.global_actions_enum[selected_index] = False
            AR.set_default("global_actions_enum.selected_indexes", [])
            AR["global_actions_enum.selected_indexes"].append(self.index)
            self['selected'] = value
        elif not (self.index in selected_indexes):
            self['selected'] = value

    selected : BoolProperty(default= False, set= set_value, get= get_value, description= "Select this Action Button", name = 'Select')
    index : IntProperty()
classes.append(AR_global_actions_enum)
# endregion