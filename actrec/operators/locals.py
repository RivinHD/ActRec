# region Imports
# external modules
import json
import uuid

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty, EnumProperty, CollectionProperty

# relative imports
from .. import functions, properties
from ..log import logger
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
        id = uuid.uuid1() if action.id in [x.id for x in AR.global_actions] else action.id
        data = { # properties 'name'(read-only), 'alert'(only temporary set) ignored
            "id" : id,
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
            "icon" : action.icon,
            "selected": True
        }
        functions.add_data_to_collection(AR.global_actions, data)
        new_action = category.actions.add()
        new_action.id = id

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
            context.area.tag_redraw()
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

class AR_OT_local_add(Operator):
    bl_idname = "ar.local_add"
    bl_label = "Add"
    bl_description = "Add a New Action"

    name : StringProperty(name= "Name", description= "Name of the Action", default= "Untitled.001")

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        new = AR.local_actions.add()
        new.id # create new id 
        new.label = functions.check_for_dublicates(map(lambda x: x.label, AR.local_actions), self.name)
        new.selected = True
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_local_add)

class AR_OT_local_remove(Operator):
    bl_idname = "ar.local_remove"
    bl_label = "Remove"
    bl_description = "Remove the selected Action"

    id : StringProperty(name= "id", description= "id of the action (1 indicator)")
    index : IntProperty(name= "index", description= "index of the action (2 indicator)", default= -1)

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.local_actions)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        if index == -1:
            self.report({'ERROR'}, "Selected Action couldn't be deleted")
            return {"CANCELLED"}
        else:
            AR.local_actions.remove(index)
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_local_remove)

class AR_OT_local_move_up(Operator):
    bl_idname = "ar.local_move_up"
    bl_label = "Move Up"
    bl_description = "Move the selected Action up"

    id : StringProperty(name= "id", description= "id of the action (1 indicator)")
    index : IntProperty(name= "index", description= "index of the action (2 indicator)", default= -1)

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.local_actions) >= 2 and AR.selected_local_action_index + 1 < len(AR.local_actions)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        if index == -1 or index + 1 >= len(AR.local_actions):
            self.report({'ERROR'}, "Selected Action couldn't be moved")
            return {"CANCELLED"}
        else:
            AR.local_actions.move(index, index + 1)
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_local_move_up)

class AR_OT_local_move_down(Operator):
    bl_idname = "ar.local_move_down"
    bl_label = "Move Down"
    bl_description = "Move the selected Action Down"
    bl_options = {"REGISTER"}

    id : StringProperty(name= "id", description= "id of the action (1 indicator)")
    index : IntProperty(name= "index", description= "index of the action (2 indicator)", default= -1)

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.local_actions) >= 2 and AR.selected_local_action_index - 1 >= 0
        
    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        if index == -1 or index - 1 >= 0:
            self.report({'ERROR'}, "Selected Action couldn't be moved")
            return {"CANCELLED"}
        else:
            AR.local_actions.move(index, index - 1)
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        return {"FINISHED"}
classes.append(AR_OT_local_move_down)

class AR_OT_local_load(Operator):
    bl_idname = "ar.local_load"
    bl_label = "Load Loacl Actions"
    bl_description = "Load the Local Action from the last Save"

    source : EnumProperty(name= 'Source', description= "Choose the source from where to load", items= [('scene', 'Scene', ''), ('text', 'Texteditor', '')])
    texts : CollectionProperty(type= properties.AR_local_load_text)

    def invoke(self, context, event):
        texts = self.texts
        texts.clear()
        for text in bpy.data.texts:
            if text.lines[0].body.strip().startswith("###AR###"):
                txt = texts.add()
                txt.name = text.name
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        logger.info("Load Local Actions")
        if self.source == 'scene':
            data = json.loads(context.scene.ar.local)
        else:
            data = []
            for text in self.texts:
                if text.apply:
                    if bpy.data.texts.find(text) == -1:
                        continue
                    text = bpy.data.texts[text]
                    lines = [line.body for line in text.lines]
                    header = {} 
                    for prop in lines[0].split("#")[-1].split(","):
                        key, value = prop.split(":")
                        header[key.strip()] = eval(value.strip())
                    commands = []
                    for line in lines[1:]:
                        split_line = line.split("#")
                        macro = {'macro': "#".join(split_line[:-1])}
                        for prop in split_line[-1].split(","):
                            key, value = prop.split(":")
                            macro[key.strip()] = eval(value.strip())
                        commands.append(macro)
                    data.append({'label': text.name, 'id': header['id'], 'commands': commands, 'icon': header['icon']})
        functions.load_local_action(AR, data)
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        self.cancel(context)
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'Source', expand= True)
        if self.Source == 'text':
            box = layout.box()
            texts = [txt.name for txt in bpy.data.texts]
            for text in self.texts:
                if text.name in texts:
                    row = box.row()
                    row.label(text= text.name)
                    row.prop(text, 'apply', text= '')

    def cancel(self, context):
        self.texts.clear()
classes.append(AR_OT_local_load)
# endregion