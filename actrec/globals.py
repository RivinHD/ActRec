# region Imports
# blender modules
import bpy
from bpy.types import Operator, PropertyGroup, AddonPreferences
from bpy.props import BoolProperty, IntProperty, CollectionProperty

# relative impotrs
from .preferences import AR_preferences
from . import categories, globals, preferences
# endregion

classes = []

# region Functions
def set_enum_index(): #Set enum, if out of range to the first enum
    AR = bpy.context.preferences.addons[__package__].preferences
    if len(AR.global_actions_enum):
        actions_selection =  AR_preferences.global_actions_selections[0] if 0 < len(AR_preferences.global_actions_selections) else 0
        enumIndex = actions_selection * (actions_selection < len(AR.global_actions_enum))
        AR.global_actions_enum[enumIndex].selected = True
# endregion

# region UI functions
def draw_actions(layout, AR, index: int) -> None:
    row = layout.row(align=True)
    row.alert = Data.alert_index == index
    row.prop(AR.category_action_enum[index], 'selected' ,toggle = 1, icon= 'LAYER_ACTIVE' if AR.category_action_enum[index].selected else 'LAYER_USED', text= "", event= True)
    row.operator(AR_OT_Category_Cmd_Icon.bl_idname, text= "", icon_value= AR.global_actions[index].icon).index = index
    row.operator(AR_OT_Category_Cmd.bl_idname , text= AR.global_actions[index].name).index = index
# endregion

# region Operators
class AR_OT_gloabal_recategorize_action(Operator):
    bl_idname = "ar.global_recategorize_action"
    bl_label = "Recategoize Action Button"
    bl_description = "Move the selected Action Button of a Category to Another Category"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.global_actions)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        categories = AR.categories
        for categorie in categories:
            if categorie.selected:
                adjust_offset = 0
                for index in AR_preferences.global_actions_selections:
                    index = index - adjust_offset
                    categorie_end = categorie.start + categorie.length
                    for current_categorie in categories:
                        if index >= current_categorie.start and index < current_categorie.start + current_categorie.length:
                            current_categorie.length -= 1
                            categories.adjust_categories(categories, current_categorie, -1)
                            break
                    data ={
                        "label": AR.global_actions[index].label,
                        "icon": AR.global_actions[index].icon,
                        "commands": [{"label": command.label, "macro": command.macro} for command in AR.global_actions[index].command]
                    }
                    AR.global_actions.remove(index)
                    Inst_Coll_Insert(categorie_end - 1 * (index < categorie_end), data, AR.global_actions)
                    adjust_offset += 1 * (index < categorie_end)
                    categorie.length += 1
                    categories.adjust_categories(categories, categorie, 1)
                globals.functions.set_enum_index()
                break
        bpy.context.area.tag_redraw()
        categories.category_runtime_save(AR)
        if AR.Autosave:
            Save()
        return {"FINISHED"}

    def draw(self, context):
        AR = context.preferences.addons[__package__].preferences
        categories = AR.Categories
        layout = self.layout
        for categorie in categories:
            layout.prop(categorie, 'selected', text= categorie.label)
classes.append(AR_OT_gloabal_recategorize_action)
# endregion

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
class Preferences(AddonPreferences):
    AR = bpy.context.preferences.addons[__package__].preferences
    AR.setdefault("global_actions_enum.selected_indexes", [])

    global_actions : CollectionProperty(type= preferences.AR_action)
    global_actions_selections = AR["global_actions_enum.selected_indexes"]
    global_actions_enum : CollectionProperty(type= AR_global_actions_enum)
# endregion

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion