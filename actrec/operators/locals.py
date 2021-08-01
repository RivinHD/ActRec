# region Imports
# external modules
import json
import uuid

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty, EnumProperty, CollectionProperty, FloatProperty

# relative imports
from .. import functions, properties, icon_manager
from ..log import logger
from . import shared
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
        return len(AR.local_actions) and not AR.local_record_macros

    def local_to_global(self, AR, category, action) -> None:
        id = uuid.uuid1() if action.id in [x.id for x in AR.global_actions] else action.id
        data = { # properties 'name'(read-only), 'alert'(only temporary set) ignored
            "id" : id,
            "label" : action.label,
            "macros" : [
                {
                    "id" : macro.id,
                    "label" : macro.label,
                    "command" : macro.command,
                    "active" : macro.active,
                    "icon" : macro.icon,
                    "is_available" : macro.is_available
                } for macro in action.macros
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

class AR_OT_local_remove(shared.id_based, Operator):
    bl_idname = "ar.local_remove"
    bl_label = "Remove"
    bl_description = "Remove the selected Action"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.local_actions) and not AR.local_record_macros

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
        self.clear()
        return {"FINISHED"}
classes.append(AR_OT_local_remove)

class AR_OT_local_move_up(shared.id_based, Operator):
    bl_idname = "ar.local_move_up"
    bl_label = "Move Up"
    bl_description = "Move the selected Action up"

    ignore_selection = False

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        return len(AR.local_actions) >= 2 and (ignore or AR.selected_local_action_index + 1 < len(AR.local_actions))

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
        self.clear()
        return {"FINISHED"}
classes.append(AR_OT_local_move_up)

class AR_OT_local_move_down(shared.id_based, Operator):
    bl_idname = "ar.local_move_down"
    bl_label = "Move Down"
    bl_description = "Move the selected Action Down"
    bl_options = {"REGISTER"}

    ignore_selection = False

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        return len(AR.local_actions) >= 2 and (ignore or AR.selected_local_action_index - 1 >= 0)
        
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
        self.clear()
        return {"FINISHED"}
classes.append(AR_OT_local_move_down)

class AR_OT_local_load(Operator):
    bl_idname = "ar.local_load"
    bl_label = "Load Loacl Actions"
    bl_description = "Load the Local Action from the last Save"

    source : EnumProperty(name= 'Source', description= "Choose the source from where to load", items= [('scene', 'Scene', ''), ('text', 'Texteditor', '')])
    texts : CollectionProperty(type= properties.AR_local_load_text)

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return not AR.local_record_macros

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
                    macros = []
                    for line in lines[1:]:
                        split_line = line.split("#")
                        macro = {'command': "#".join(split_line[:-1])}
                        for prop in split_line[-1].split(","):
                            key, value = prop.split(":")
                            macro[key.strip()] = eval(value.strip())
                        macros.append(macro)
                    data.append({'label': text.name, 'id': header['id'], 'macros': macros, 'icon': header['icon']})
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

class AR_OT_local_selection_up(Operator):
    bl_idname = 'ar.local_selection_up'
    bl_label = 'ActRec Selection Up'

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.selected_local_action_index = AR.selected_local_action_index - 1
        context.area.tag_redraw()
        return{'FINISHED'}
classes.append(AR_OT_local_selection_up)

class AR_OT_local_selection_down(Operator):
    bl_idname = 'ar.local_selection_down'
    bl_label = 'ActRec Selection Down'
    
    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.selected_local_action_index = AR.selected_local_action_index + 1
        context.area.tag_redraw()
        return{'FINISHED'}
classes.append(AR_OT_local_selection_up)

class AR_OT_local_play(shared.id_based, Operator):
    bl_idname = 'ar.local_play'
    bl_label = 'ActRec Play'
    bl_description = 'Play the selected Action.'
    bl_options = {'REGISTER','UNDO'}

    ignore_selection = False

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        return (len(AR.local_actions[AR.selected_local_action_index].macros) or ignore) and not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        action = AR.local_actions[index]
        functions.play(action.macros, action, 'local_actions')
        self.clear()
        return{'FINISHED'}
classes.append(AR_OT_local_play)

class AR_OT_add_event(shared.id_based, Operator):
    bl_idname = "ar.add_event"
    bl_label = "Add Event"
    bl_description = "Add a Event which wait until the Event is Triggered"
    
    ignore_selection = False

    types = [
        ('Timer', 'Timer', 'Wait the chosen Time and continue with the Macros', 'SORTTIME', 0),
        ('Render Complet', 'Render complet', 'Wait until the rendering has finished', 'IMAGE_RGB_ALPHA', 1),
        ('Render Init', 'Render Init', 'Wait until the rendering has started', 'IMAGE_RGB', 2),
        ('Loop', 'Loop', 'Loop the conatining Makros until the Statment is False \nNote: The Loop need the EndLoop Event to work, otherwise the Event get skipped', 'FILE_REFRESH', 3),
        ('EndLoop', 'EndLoop', 'Ending the latetest called loop, when no Loop Event was called this Event get skipped', 'FILE_REFRESH', 4),
        ('Clipboard', 'Clipboard', 'Adding a command with the data from the Clipboard', 'CONSOLE', 5),
        ('Empty', 'Empty', 'Crates an Empty Macro', 'SHADING_BBOX', 6),
        ('Select Object', 'Select Object', 'Select the choosen object', 'OBJECT_DATA', 7)
    ]
    type : EnumProperty(items= types, name= "Event Type", description= 'Shows all possible Events', default= 'Empty')

    time : FloatProperty(name= "Time", description= "Time in Seconds", unit='TIME')
    statements : EnumProperty(items=[('count', 'Count', 'Count a Number from the Start with the Step to the End, \nStop when Number > End', '', 0),
                                    ('python', 'Python Statment', 'Create a custom statement with python code', '', 1)])
    start : FloatProperty(name= "Start", description= "Start of the Count statements", default=0)
    end : FloatProperty(name= "End", description= "End of the Count statements", default= 1)
    step: FloatProperty(name= "Step", description= "Step of the Count statements", default= 1)
    python_statement : StringProperty(name= "Statement", description= "Statment for the Python Statement")
    object : StringProperty(name= "Object", description= "Choose an Object which get select when this Event is played")

    macro_index : IntProperty(name= "Macro Index", default= -1)

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        return (len(AR.local_actions[AR.selected_local_action_index].macros) or ignore) and not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        action = AR.local_actions[index]
        if self.macro_index == -1:
            macro = action.macros.add()
        else:
            macro = action.macros[self.macro_index]

        if self.type == 'Clipboard':
            clipboard = context.window_manager.clipboard
            name = functions.get_name_of_command(clipboard)
            macro.label = name if isinstance(name, str) else clipboard
            macro.command = clipboard
        elif self.type == 'Empty':
            macro.label = "<Empty>"
            macro.command = ""
            bpy.ops.ar.command_edit('INVOKE_DEFAULT', index= index, Edit= True)
        else:
            macro.label = "Event: %s" %self.type
            data = {'Type': self.type}
            if self.type == 'Timer':
                data['Time'] = self.time
            elif self.type == 'Loop':
                data['StatementType'] = self.statements
                if self.statements == 'python':
                    data["PyStatement"] = self.python_statement
                else:
                    data["Startnumber"] = self.start
                    data["Endnumber"] = self.end
                    data["Stepnumber"] = self.step
            elif self.type == 'Select Object':
                data['Object'] = self.object
            macro.command = "ar.event: %s" %json.dumps(data)
        functions.local_runtime_save(AR, context.scene)
        if not AR.hide_local_text:
            functions.local_action_to_text(action)
        self.clear()
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'type')
        if self.type == 'Timer':
            box = layout.box()
            box.prop(self, 'time')
        elif self.type == 'Loop':
            box = layout.box()
            box.prop(self, 'statements')
            box.separator()
            if self.statements == 'python':
                box.prop(self, 'python_statement')
            else:
                box.prop(self, 'start')
                box.prop(self, 'end')
                box.prop(self, 'step')
        elif self.type == 'Select Object':
            box = layout.box()
            box.prop_search(self, 'object', context.view_layer, 'objects')

    def invoke(self, context, event):
        if context.object != None:
            self.object = context.object.name
        return context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_add_event)

class AR_OT_record(shared.id_based, Operator):
    bl_idname = "ar.record"
    bl_label = "Start/Stop Recording"

    ignore_selection = False
    record_start_index : IntProperty()

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        return (len(AR.local_actions[AR.selected_local_action_index].macros) or ignore)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.local_record_macros = not AR.local_record_macros
        index = functions.get_local_action_index(AR, self.id, self.index)
        action = AR.local_actions[index]
        if AR.local_record_macros: # start recording
            self.id = action.id
            self.index = index
            self.record_start_index = self.get_report_text(context).count('\n')
        else: # end recording and add reports as macros
            reports = self.get_report_text(context).splitlines()[self.record_start_index: ]
            operators = []
            compare_operators = False
            error_reports = []
            for report in [report for report in reports if report.startswith('bpy.')]:
                ret = functions.add_report_as_macro(action, report, operators, compare_operators, error_reports)
                if ret:
                    compare_operators = ret
            if error_reports:
                self.report({'ERROR'}, "Not all reports could be added added:\n%s" %"\n".join(error_reports))
            functions.local_runtime_save(AR, context.scene)
            functions.local_action_to_text(action)
            context.area.tag_redraw()
            self.clear()
        return {"FINISHED"}
    
    @classmethod
    def description(cls, context, properties):
        AR = context.preferences.addons[__package__].preferences
        if AR.local_record_macros:
            return "Stops Recording the Macros"
        return "Starts Recording the Macros"
classes.append(AR_OT_record)

class AR_OT_local_icon(icon_manager.icontable, shared.id_based, Operator):
    bl_idname = "ar.local_icon"

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.local_actions[self.id].icon = AR.selected_icon
        AR.selected_icon = 0 #Icon: NONE
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        self.clear()
        return {"FINISHED"}

    def invoke(self, context, event):
        AR = context.preferences.addons[__package__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        action = AR.local_actions[index]
        self.id = action.id
        AR.selected_icon = action.icon
        self.search = ''
        return context.window_manager.invoke_props_dialog(self, width=1000)
# endregion