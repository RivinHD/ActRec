# region Imports
# external modules
import ensurepip
import os
import subprocess
import importlib
import json
import time

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty, EnumProperty, CollectionProperty, FloatProperty, BoolProperty

# relative imports
from . import shared
from .. import functions, properties
from ..log import logger
# endregion

__module__ = __package__.split(".")[0]

# region Operators
class macro_based(shared.id_based):
    action_index : IntProperty(default= -1)
    ignore_selection = False

    def clear(self):
        self.action_index = -1
        super().clear()

class AR_OT_macro_add(shared.id_based, Operator):
    bl_idname = "ar.macro_add"
    bl_label = "ActRec Add Macro"
    bl_description = "Add the last operation you executed"

    command : StringProperty(default= "")
    report_length : IntProperty(default= 0)

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        return len(AR.local_actions)

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        AR.local_record_macros = not AR.local_record_macros
        index = functions.get_local_action_index(AR, self.id, self.index)
        action = AR.local_actions[index]
        new_report = False
        if not self.command:
            reports = functions.get_report_text(context).splitlines()
            length = len(reports)
            if self.report_len != length:
                new_report = True
                self.report_length = length
                reports.reverse()
                for report in reports:
                    if report.startswith("bpy.ops.") or report.startswith("bpy.context."):
                        self.command = report
                        break
        
        command = self.command
        if command and (AR.last_macro_command != command if new_report else True):
            if command.startswith("bpy.context."):
                while bpy.ops.ed.undo.poll():
                    source_path, attribute, value = functions.split_context_report(command)
                    copy_dict = functions.create_object_copy(context, source_path, attribute)
                    bpy.ops.ed.undo()
                    context = bpy.context
                    ret = functions.improve_context_report(context, copy_dict, source_path, attribute, value)
                    if ret:
                        command = ret
                        break
            
            while bpy.ops.ed.redo.poll():
                bpy.ops.ed.redo()

            functions.add_report_as_macro(AR, action, command, [], None, [])
        else:
            if new_report:
                self.report({'ERROR'}, "No Action could be added")
            if AR.local_create_empty:
                bpy.ops.ar.macro_add_event("EXEC_DEFAULT", id= action.id, index= index, type= "Empty")
        functions.local_runtime_save(AR, context.scene)
        bpy.context.area.tag_redraw()
        self.clear()
        self.command = ""
        return {"FINISHED"}

class AR_OT_macro_add_event(shared.id_based, Operator):
    bl_idname = "ar.macro_add_event"
    bl_label = "Add Event"
    bl_description = "Add a Event to the selected Action"

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
    statement_type : EnumProperty(items=[('count', 'Count', 'Count a Number from the Start with the Step to the End, \nStop when Number > End', '', 0),
                                    ('python', 'Python Statment', 'Create a custom statement with python code', '', 1)])
    start : FloatProperty(name= "Start", description= "Start of the Count statements", default=0)
    end : FloatProperty(name= "End", description= "End of the Count statements", default= 1)
    step: FloatProperty(name= "Step", description= "Step of the Count statements", default= 1)
    python_statement : StringProperty(name= "Statement", description= "Statment for the Python Statement")
    object : StringProperty(name= "Object", description= "Choose an Object which get select when this Event is played")

    macro_index : IntProperty(name= "Macro Index", default= -1)

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        return len(AR.local_actions) and not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        action = AR.local_actions[index]
        if self.macro_index == -1:
            macro = action.macros.add()
        else:
            macro = action.macros[self.macro_index]
            self.macro_index = -1

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
                data['StatementType'] = self.statement_type
                if self.statement_type == 'python':
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

class AR_OT_macro_remove(macro_based, Operator):
    bl_idname = "ar.macro_remove"
    bl_label = "Remove Macro"
    bl_description = "Remove the selected Macro"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        return len(AR.local_actions) and (len(AR.local_actions[AR.selected_local_action_index].macros) or ignore) and not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        action_index = functions.get_local_action_index(AR, '', self.action_index)
        action = AR.local_actions[action_index]
        index = functions.get_local_macro_index(action, self.id, self.index)
        action.macros.remove(index)
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        self.clear()
        return {"FINISHED"}

class AR_OT_macro_move_up(macro_based, Operator):
    bl_idname = "ar.macro_move_up"
    bl_label = "Move Macro Up"
    bl_description = "Move the selected Macro up"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        if not len(AR.local_actions):
            return False
        action = AR.local_actions[AR.selected_local_action_index]
        return (len(action.macros) >= 2 and action.selected_macro_index + 1 < len(action.macros) or ignore) and not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        action_index = functions.get_local_action_index(AR, '', self.action_index)
        action = AR.local_actions[action_index]
        index = functions.get_local_macro_index(action, self.id, self.index)
        self.clear()
        if index == -1 or index + 1 >= len(action.macros):
            self.report({'ERROR'}, "Selected Action couldn't be moved")
            return {"CANCELLED"}
        else:
            action.macros.move(index, index + 1)
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        return {"FINISHED"}

class AR_OT_macro_move_down(macro_based, Operator):
    bl_idname = "ar.macro_move_down"
    bl_label = "Move Macro Down"
    bl_description = "Move the selected Macro down"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        if not len(AR.local_actions):
            return False
        action = AR.local_actions[AR.selected_local_action_index]
        return (len(action.macros) >= 2 and action.selected_macro_index - 1 >= 0 or ignore) and not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        action_index = functions.get_local_action_index(AR, '', self.action_index)
        action = AR.local_actions[action_index]
        index = functions.get_local_macro_index(action, self.id, self.index)
        self.clear()
        if index == -1 or index - 1 >= 0:
            self.report({'ERROR'}, "Selected Action couldn't be moved")
            return {"CANCELLED"}
        else:
            action.macros.move(index, index - 1)
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        return {"FINISHED"}

class text_analysis():
    def __init__(self, fontpath):
        self.path = fontpath
        # install the fonttools to blender modules if not exists
        if importlib.util.find_spec('fontTools') is None:
            ensurepip.bootstrap()
            os.environ.pop("PIP_REQ_TRACKER", None)
            try:
                output = subprocess.check_output([bpy.app.binary_path_python, '-m', 'pip', 'install', 'fonttools', '--no-color'])
                logger.info(output)
            except subprocess.CalledProcessError as e:
                logger.warning(e.output)
                self.use_dynamic_text = False
                return
        self.use_dynamic_text = True
        from fontTools.ttLib import TTFont

        font = TTFont(fontpath)
        self.t = font['cmap'].getcmap(3,1).cmap
        self.s = font.getGlyphSet()
        self.width_in_pixels = 10/font['head'].unitsPerEm
    
    def get_width_of_text(self, text):
        total = []
        for c in text:
            total.append(self.s[self.t[ord(c)]].width * self.width_in_pixels)
        return total
    
class AR_OT_macro_edit(macro_based, Operator):
    bl_idname = "ar.macro_edit"
    bl_label = "Edit"
    bl_description = "Double click to Edit"

    label : StringProperty(name= "Label")
    command : StringProperty(name= "Command")
    last_id : StringProperty(name= "Last Id")
    time : FloatProperty(name= "Time", description= "last execution time, used to detect double click")
    edit : BoolProperty(default= False)
    copy_data : BoolProperty(default= False, name= "Copy Previous", description= "Copy the data of the previous recorded Macro and place it in this Macro")
    lines : CollectionProperty(type= properties.AR_macro_multiline)
    active_line : IntProperty(default= 0)
    width = 500
    font_text = None

    def invoke(self, context, event):
        AR = context.preferences.addons[__module__].preferences
        action_index = self.action_index = functions.get_local_action_index(AR, '', self.action_index)
        action = AR.local_actions[action_index]
        index = self.index = functions.get_local_macro_index(action, self.id, self.index)
        macro = action.macros[index]

        t = time.time()
        if self.last_id == macro.id and self.time + 0.7 > t or self.edit:
            self.last_id = macro.id
            self.time = t
            split = macro.command.split(":")
            if split[0] == 'ar.event':
                data = json.loads(":".join(split[1:]))
                if data['Type'] == 'Timer':
                    bpy.ops.ar.macro_add_event('INVOKE_DEFAULT', type= data['Type'], macro_index= self.index, time= data['Time'])
                elif data['Type'] == 'Loop':
                    if data['StatementType'] == 'python':
                        bpy.ops.ar.macro_add_event('INVOKE_DEFAULT', type= data['Type'], macro_index= self.index, statement_type= data['StatementType'], python_statement= data["PyStatement"])
                    else:
                        bpy.ops.ar.macro_add_event('INVOKE_DEFAULT', type= data['Type'], macro_index= self.index, statement_type= data['StatementType'], start= data["Startnumber"], end= data["Endnumber"], step= data["Stepnumber"])
                elif data['Type'] == 'Select Object':
                    bpy.ops.ar.macro_add_event('INVOKE_DEFAULT', type= data['Type'], macro_index= self.index, object= data['Object'])
                else:
                    bpy.ops.ar.macro_add_event('INVOKE_DEFAULT', type= data['Type'], macro_index= self.index)
                self.clear()
                return {"FINISHED"}
            self.label = macro.label
            self.command = macro.command
            fontpath = functions.get_font_path()
            if self.font_text is None or self.font_text.path != fontpath:
                self.font_text = text_analysis(fontpath)
            self.lines.clear()
            for line in functions.text_to_lines(self.command, self.font_text, self.width - 15):
                new = self.lines.add()
                new.text = line
            return context.window_manager.invoke_props_dialog(self, width=self.width)
        else:
            self.last_id = macro.id
            self.time = t
            action.selected_macro_index = index
        self.clear()
        return {"FINISHED"}

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        action = AR.local_actions[self.action_index]
        macro = action.macros[self.index]
        if self.copy_data:
            macro.label = AR.last_macro_label
            macro.command = AR.last_macro_command
        else:
            macro.label = self.label
            macro.command = self.command
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        self.cancel(context)
        return {"FINISHED"}

    def draw(self, context):
        AR = context.preferences.addons[__module__].preferences
        layout = self.layout
        self.command = ""
        for line in self.text:
            self.command += line.line
        command = ""
        if self.copy_data:
            layout.prop(AR, 'last_macro_label', text= "Label")
            command = AR.last_macro_command
        else:
            layout.prop(self, 'label', text= "Label")
            command = self.command
        self.text.clear()
        for line in functions.text_to_lines(command, self.font_text, self.width - 16): # 8 left and right of the Stringproperty begins text
            new = self.lines.add()
            new.text = line
        col = layout.column(align= True)
        for line in self.text:
            col.prop(line, 'line', text= "")
        row = layout.row().split(factor= 0.65)
        ops = row.operator("ar.macros_clear_ops")
        ops.edit_operator = self
        row.prop(self, 'copy_data', toggle= True)

    def cancel(self, context):
        self.edit = False
        self.copy_data = False
        self.clear()

class AR_OT_macros_clear_ops(Operator):
    bl_idname = "ar.macros_clear_ops"
    bl_label = "Clear Operator"
    bl_options = {'INTERNAL'}

    edit_operator = None
    
    def execute(self, context):
        ops = self.edit_operator
        if ops:
            ops.command = "()%s" %ops.command.split("(")[0]
        return {"FINISHED"}

class AR_OT_copy_to_actrec(Operator):
    bl_idname = "ar.copy_to_actrec"
    bl_label = "Copy to Action Recorder"
    bl_description = "Copy the selected Operator to Action Recorder Macro"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        return bpy.ops.ui.copy_python_command_button.poll() and len(AR.local_actions)

    def execute(self, context):
        clipboard = context.window_manager.clipboard
        bpy.ops.ui.copy_python_command_button(context)
        bpy.ops.ar.macro_add('EXEC_DEFAULT', command= context.window_manager.clipboard)
        context.window_manager.clipboard = clipboard
        return {"FINISHED"}
# endregion

classes = [
    AR_OT_macro_add,
    AR_OT_macro_add_event,
    AR_OT_macro_remove,
    AR_OT_macro_move_up,
    AR_OT_macro_move_down,
    AR_OT_macro_edit,
    AR_OT_macros_clear_ops,
    AR_OT_copy_to_actrec
]

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion