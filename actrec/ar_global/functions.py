# region Import
# blender modules
import bpy
# relativ imports
from ..preferences import AR_preferences
# endregion


# region Functions
def set_enum_index(): #Set enum, if out of range to the first enum
    AR = bpy.context.preferences.addons[__package__].preferences
    if len(AR.global_actions_enum):
        actions_selection =  AR_preferences.global_actions_selections[0] if 0 < len(AR_preferences.global_actions_selections) else 0
        enumIndex = actions_selection * (actions_selection < len(AR.global_actions_enum))
        AR.global_actions_enum[enumIndex].selected = True

# endregion
