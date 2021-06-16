# region Imports
# blender modules
import bpy
# endregion

# region Functions
def set_enum_index(): #Set enum, if out of range to the first enum
    AR = bpy.context.preferences.addons[__package__].preferences
    if len(AR.global_actions_enum):
        global_actions_selections= AR.get("global_actions_enum.selected_indexes", [0])
        actions_selection = global_actions_selections[0] if 0 < len(global_actions_selections) else 0
        enumIndex = actions_selection * (actions_selection < len(AR.global_actions_enum))
        AR.global_actions_enum[enumIndex].selected = True
# endregion