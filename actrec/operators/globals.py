# region Imports
# blender modules
import bpy
from bpy.types import Operator
# endregion

classes = []

# region Operators
class AR_OT_gloabal_recategorize_action(Operator):
    bl_idname = "ar.global_recategorize_action"
    bl_label = "Recategoize Action Button"
    bl_description = "Move the selected Action Button of a Category to Another Category"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.global_actions)

    def invoke(self, context: bpy.context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.context):
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

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion