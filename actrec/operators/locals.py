# region Imports
# external modules
import json
import uuid

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, IntProperty, EnumProperty, CollectionProperty

# relative imports
from .. import functions, properties, icon_manager
from ..log import logger
from . import shared
# endregion

__module__ = __package__.split(".")[0]

# region Operators
class AR_OT_local_to_global(Operator):
    bl_idname = "ar.local_to_global"
    bl_label = "Local Action to Global"
    bl_description = "Transfer the selected Action to Global-actions"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        return len(AR.local_actions) and not AR.local_record_macros

    def local_to_global(self, AR, category, action) -> None:
        id = uuid.uuid1() if action.id in [x.id for x in AR.global_actions] else action.id
        data = functions.property_to_python(action, exclude= ["name", "alert", "macros.name", "macros.alert", "macros.is_available"])
        data["id"] = id
        data["selected"] = True
        functions.add_data_to_collection(AR.global_actions, data)
        new_action = category.actions.add()
        new_action.id = id

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
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
        AR = context.preferences.addons[__module__].preferences
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

class AR_OT_local_add(Operator):
    bl_idname = "ar.local_add"
    bl_label = "Add"
    bl_description = "Add a New Action"

    name : StringProperty(name= "Name", description= "Name of the Action", default= "Untitled.001")

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        new = AR.local_actions.add()
        new.id # create new id 
        new.label = functions.check_for_dublicates(map(lambda x: x.label, AR.local_actions), self.name)
        new.selected = True
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        return {"FINISHED"}

class AR_OT_local_remove(shared.id_based, Operator):
    bl_idname = "ar.local_remove"
    bl_label = "Remove"
    bl_description = "Remove the selected Action"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        return len(AR.local_actions) and not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        self.clear()
        if index == -1:
            self.report({'ERROR'}, "Selected Action couldn't be deleted")
            return {"CANCELLED"}
        else:
            AR.local_actions.remove(index)
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        return {"FINISHED"}

class AR_OT_local_move_up(shared.id_based, Operator):
    bl_idname = "ar.local_move_up"
    bl_label = "Move Up"
    bl_description = "Move the selected Action up"

    ignore_selection = False

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        return len(AR.local_actions) >= 2 and (ignore or AR.selected_local_action_index + 1 < len(AR.local_actions))

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        self.clear()
        if index == -1 or index + 1 >= len(AR.local_actions):
            self.report({'ERROR'}, "Selected Action couldn't be moved")
            return {"CANCELLED"}
        else:
            AR.local_actions.move(index, index + 1)
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        return {"FINISHED"}
        
    def cancel(self, context):
        self.clear()

class AR_OT_local_move_down(shared.id_based, Operator):
    bl_idname = "ar.local_move_down"
    bl_label = "Move Down"
    bl_description = "Move the selected Action Down"
    bl_options = {"REGISTER"}

    ignore_selection = False

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        return len(AR.local_actions) >= 2 and (ignore or AR.selected_local_action_index - 1 >= 0)
        
    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        self.clear()
        if index == -1 or index - 1 >= 0:
            self.report({'ERROR'}, "Selected Action couldn't be moved")
            return {"CANCELLED"}
        else:
            AR.local_actions.move(index, index - 1)
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        return {"FINISHED"}

    def cancel(self, context):
        self.clear()

class AR_OT_local_load(Operator):
    bl_idname = "ar.local_load"
    bl_label = "Load Loacl Actions"
    bl_description = "Load the Local Action from the last Save"

    source : EnumProperty(name= 'Source', description= "Choose the source from where to load", items= [('scene', 'Scene', ''), ('text', 'Texteditor', '')])
    texts : CollectionProperty(type= properties.AR_local_load_text)

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
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
        AR = context.preferences.addons[__module__].preferences
        logger.info("Load Local Actions")
        if self.source == 'scene':
            data = json.loads(context.scene.ar.local)
            if not isinstance(data, list):
                self.report({'ERROR'}, "scenedata couldn't be loaded")
                return {'CANCELLED'}
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
        layout.prop(self, 'source', expand= True)
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

class AR_OT_local_selection_up(Operator):
    bl_idname = 'ar.local_selection_up'
    bl_label = 'ActRec Selection Up'

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        return not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        AR.selected_local_action_index = AR.selected_local_action_index - 1
        context.area.tag_redraw()
        return{'FINISHED'}

class AR_OT_local_selection_down(Operator):
    bl_idname = 'ar.local_selection_down'
    bl_label = 'ActRec Selection Down'
    
    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        return not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        AR.selected_local_action_index = AR.selected_local_action_index + 1
        context.area.tag_redraw()
        return{'FINISHED'}

class AR_OT_local_play(shared.id_based, Operator):
    bl_idname = 'ar.local_play'
    bl_label = 'ActRec Play'
    bl_description = 'Play the selected Action.'
    bl_options = {'REGISTER','UNDO'}

    ignore_selection = False

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        return len(AR.local_actions) and (len(AR.local_actions[AR.selected_local_action_index].macros) or ignore) and not AR.local_record_macros

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        action = AR.local_actions[index]
        functions.play(context.copy(), action.macros, action, 'local_actions')
        self.clear()
        return{'FINISHED'}

class AR_OT_local_record(shared.id_based, Operator):
    bl_idname = "ar.local_record"
    bl_label = "Start/Stop Recording"

    ignore_selection = False
    record_start_index : IntProperty()

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        return len(AR.local_actions)

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        AR.local_record_macros = not AR.local_record_macros
        index = functions.get_local_action_index(AR, self.id, self.index)
        action = AR.local_actions[index]
        if AR.local_record_macros: # start recording
            self.id = action.id
            self.index = index
            self.record_start_index = functions.get_report_text(context).count('\n')
            context.scene.ar.record_undo_end = not context.scene.ar.record_undo_end
        else: # end recording and add reports as macros
            reports = functions.get_report_text(context)
            reports = [report for report in reports if report.startswith('bpy.')]

            record_undo_end = context.scene.ar.record_undo_end
            while record_undo_end == bpy.context.scene.ar.record_undo_end and bpy.ops.ed.undo.poll():
                bpy.ops.ed.undo()
            context = bpy.context
            i = 0
            while bpy.ops.ed.redo.poll():
                report = reports[i]
                if report.startswith("bpy.context."):
                    source_path, attribute, value = functions.split_context_report(report)
                    copy_dict = functions.create_object_copy(context, source_path, attribute)

                    bpy.ops.ed.redo()
                    context = bpy.context
                    
                    report = functions.improve_context_report(context, copy_dict, source_path, attribute, value)
                    if report:
                        reports[i] = report
                        i += 1
                elif report.startswith("bpy.ops."):
                    pass
                else:
                    i += 1

            operators = []
            compare_operators = None
            error_reports = []
            for report in reports:
                ret = functions.add_report_as_macro(AR, action, report, operators, compare_operators, error_reports)
                if ret:
                    compare_operators = ret
            if error_reports:
                self.report({'ERROR'}, "Not all reports could be added added:\n%s" %"\n".join(error_reports))
            functions.local_runtime_save(AR, bpy.context.scene)
            functions.local_action_to_text(action)
            context.area.tag_redraw()
            self.clear()
        return {"FINISHED"}
    
    @classmethod
    def description(cls, context, properties):
        AR = context.preferences.addons[__module__].preferences
        if AR.local_record_macros:
            return "Stops Recording the Macros"
        return "Starts Recording the Macros"

class AR_OT_local_icon(icon_manager.icontable, shared.id_based, Operator):
    bl_idname = "ar.local_icon"

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        AR.local_actions[self.id].icon = AR.selected_icon
        AR.selected_icon = 0 #Icon: NONE
        self.reuse = False
        functions.local_runtime_save(AR, context.scene)
        context.area.tag_redraw()
        self.clear()
        return {"FINISHED"}

    def invoke(self, context, event):
        AR = context.preferences.addons[__module__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        action = AR.local_actions[index]
        self.id = action.id
        if not self.reuse:
            AR.selected_icon = action.icon
        self.search = ''
        return context.window_manager.invoke_props_dialog(self, width=1000)

class AR_OT_local_clear(shared.id_based, Operator):
    bl_idname = "ar.local_clear"
    bl_label = "Clear Macros"
    bl_description = "Delete all Macro of the selected Action"

    ignore_selection = False

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__module__].preferences
        ignore = cls.ignore_selection
        cls.ignore_selection = False
        return len(AR.local_actions) and (len(AR.local_actions[AR.selected_local_action_index].macros) or ignore)

    def execute(self, context):
        AR = context.preferences.addons[__module__].preferences
        index = functions.get_local_action_index(AR, self.id, self.index)
        AR.local_actions[index].macros.clear()
        functions.local_runtime_save(AR, context.scene)
        bpy.context.area.tag_redraw()
        self.clear()
        return {"FINISHED"}
# endregion

classes = [
    AR_OT_local_to_global,
    AR_OT_local_add,
    AR_OT_local_remove,
    AR_OT_local_move_up,
    AR_OT_local_move_down,
    AR_OT_local_load,
    AR_OT_local_selection_up,
    AR_OT_local_selection_down,
    AR_OT_local_play,
    AR_OT_local_record,
    AR_OT_local_icon,
    AR_OT_local_clear
]

# region Registration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion