# region Imports
# blender modules
import bpy
from bpy.types import Operator

# relative imports
from .. import functions
# endregion

classes = []

# region Operators
class AR_OT_local_to_global(Operator):
    bl_idname = "ar.local_to_global"
    bl_label = "Action to Global"
    bl_description = "Add the selected Action to a Category"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.local_actions)

    def local_to_global(self, AR, category, action) -> None:
        data = { # properties 'name'(read-only), 'alert'(only temporary set) ignored
            "id" : action.id,
            "label" : action.label,
            "commands" : [
                {
                    "id" : command.id,
                    "label" : command.label,
                    "macro" : command.macro,
                    "active" : command.active,
                    "icon" : command.icon,
                    "is_available" : command.is_available
                } for command in action.commands
            ],
            "icon" : action.icon
        }
        functions.insert_to_collection(AR.categories, AR['categories.selected_index'], data)
        category.length += 1
        functions.add_global_actions_enum(AR)
        functions.adjust_categories(AR.categories, category, 1)


    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        categories = AR.categories
        if len(categories):
            for category in categories:
                if category.selected:
                    self.local_to_global(AR, category, AR.local_actions[AR.selected_local_action_index])
                    break
            if AR.local_to_global_mode == 'move':
                AR.local_actions.remove(AR.selected_local_action_index)
            functions.category_runtime_save(AR)
            functions.global_runtime_save(AR, autosave= False)
            bpy.context.area.tag_redraw()
            return {"FINISHED"}
        else:
            return {'CANCELLED'}

    def draw(self, context):
        AR = context.preferences.addons[__package__].preferences
        categories = AR.categories
        layout = self.layout
        if len(categories):
            for category in categories:
                layout.prop(category, 'selected', text= category.label)
        else:
            box = layout.box()
            col = box.column()
            col.scale_y = 0.9
            col.label(text= 'Please Add a Category first', icon= 'INFO')
            col.label(text= 'To do that, go to the Advanced menu', icon= 'BLANK1')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_local_to_global)
# endregion