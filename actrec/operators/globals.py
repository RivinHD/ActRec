# region Imports
# external modules
import os
from typing import Optional
import zipfile
from collections import defaultdict
import uuid
import json

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty, CollectionProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

# relative imports
from .. import functions, properties
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
        return len(AR.global_actions) and len(AR.get("global_actions_enum.selected_indexes", []))

    def invoke(self, context: bpy.context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.context):
        AR = context.preferences.addons[__package__].preferences
        categories = AR.categories
        for category in categories:
            if category.selected:
                adjust_offset = 0
                for index in AR["global_actions_enum.selected_indexes"]:
                    index = index - adjust_offset
                    categorie_end = category.start + category.length
                    for current_categorie in categories:
                        if index >= current_categorie.start and index < current_categorie.start + current_categorie.length: # change length of category of selected action
                            current_categorie.length -= 1
                            functions.adjust_categories(categories, current_categorie, -1)
                            break
                    AR.global_actions.move(index, categorie_end - 1 * (index < categorie_end))
                    adjust_offset += 1 * (index < categorie_end)
                    category.length += 1
                    functions.adjust_categories(categories, category, 1)
                functions.set_enum_index(AR)
                bpy.context.area.tag_redraw()
                functions.global_runtime_save(AR)
                return {"FINISHED"}
        return {'CANCELLED'}

    def draw(self, context):
        AR = context.preferences.addons[__package__].preferences
        categories = AR.Categories
        layout = self.layout
        for category in categories:
            layout.prop(category, 'selected', text= category.label)
classes.append(AR_OT_gloabal_recategorize_action)

class AR_OT_global_import(Operator, ImportHelper):
    bl_idname = "ar.global_import"
    bl_label = "Import"
    bl_description = "Import the Action file into the storage"

    filter_glob: StringProperty(default='*.zip;*.json', options={'HIDDEN'})

    category : StringProperty(default= "Imports")
    mode : EnumProperty(name= 'Mode', items= [("add","Add",""),("overwrite", "Overwrite", "")])

    def get_commands_from_file(self, zip_file: zipfile.ZipFile, path: str) -> list:
        lines = zip_file.read(path).splitlines(False)
        commands = []
        for line in lines:
            split_line = line.split("#")
            data = {'id' : uuid.uuid1().hex, 'active' : True, 'icon': 101}
            if len(split_line) >= 2:
                data['macro'] = "#".join(split_line[:-1])
                data['label'] = split_line[-1]
            else:
                data['macro'] = split_line[0]
                label = functions.get_name_of_command(split_line[0])
                data['label'] = label if isinstance(label, str) else split_line[0]
            commands.append(data)
        return commands

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences

        if AR.import_extension == ".zip":
            if not len(AR.import_settings) and bpy.ops.ar.global_import_settings('EXEC_DEFAULT', filepath= self.filepath, from_operator= True) == {'CANCELLED'}:
                self.report({'ERROR'}, "The selected file is not compatible")
                return {'CANCELLED'}

            data = defaultdict(list)
            current_actions_length = 0
            zip_file = zipfile.ZipFile(self.filepath, mode= 'r')
            for category in AR.import_settings:
                if category.use and any(action.use for action in category.actions):
                    actions = list(filter(lambda x: x.use, category.actions))
                    data['categories'].append({
                        'id' : uuid.uuid1().hex,
                        'label' : category.label,
                        'start' : current_actions_length,
                        'length' : len(actions),
                    })
                    for action in actions:
                        data['actions'].append({
                        'id' : uuid.uuid1().hex,
                        'label' : action.label,
                        'commands' : self.get_commands_from_file(zip_file, action.identifier),
                        'icon' : action.identifier.split("~")[-1]
                        })
            functions.import_global_from_dict(AR, data)
        elif AR.import_extension == ".json":
            if not len(AR.import_settings) and bpy.ops.ar.global_import_settings('EXEC_DEFAULT', filepath= self.filepath, from_operator= True) == {'CANCELLED'}:
                self.report({'ERROR'}, "The selected file is not compatible")
                return {'CANCELLED'}

            with open(self.filepath, 'r', encoding= 'utf-8') as file:
                data = json.loads(file.read())
            category_ids = set(category.identifier for category in AR.import_settings)
            action_ids = []
            for category in AR.import_settings:
                action_ids += [action.identifier for action in category.actions]
            action_ids = set(action_ids)

            data['categories'] = [category for category in data['categories'] if category['id'] not in category_ids]
            data['actions'] = [action for action in data['actions'] if action['id'] not in action_ids]
            functions.import_global_from_dict(AR, data)
        else:
            self.report({'ERROR'}, "Select a .json or .zip file {%s}" %self.filepath)
        AR = context.preferences.addons[__package__].preferences
        AR.import_settings.clear()
        functions.category_runtime_save(AR)
        functions.global_runtime_save(AR, False)
        return {"FINISHED"}

    def draw(self, context):
        AR = context.preferences.addons[__package__].preferences
        layout = self.layout
        layout.operator("ar.global_import_settings", text= "Load Importsettings").filepath = self.filepath
        col = layout.column(align= True)
        row = col.row(align=True)
        row.prop(self, 'mode', expand= True)
        for category in AR.import_settings:
            box = col.box()
            sub_col = box.column()
            row = sub_col.row()
            if category.show:
                row.prop(category, 'show', icon="TRIA_DOWN", text= "", emboss= False)
            else:
                row.prop(category, 'show', icon="TRIA_RIGHT", text= "", emboss= False)
            row.prop(category, 'use', text= "")
            row.label(text= category.label)
            row.prop(category, 'mode', text= "", expand= True)
            if category.show:
                sub_col = box.column()
                for action in category.actions:
                    row = sub_col.row()
                    row.prop(action, 'use', text= "")
                    row.label(text= action.label)
        
    def cancel(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.import_settings.clear()
classes.append(AR_OT_global_import)

class AR_OT_global_import_settings(Operator):
    bl_idname = "ar.global_import_settings"
    bl_label = "Load Importsettings"
    bl_description = "Load the select the file to change the importsettings"

    filepath : StringProperty()
    from_operator : BoolProperty(default= False)

    def valid_file(self, file: str) -> bool:
        if file.endswith(".py") and file.count('~') == 2:
            index, name, icon = file.split("~")
            return index.isdigit() and (icon.isupper() or icon.isdigit())
        return False
    
    def valid_directory(self, directroy: str) -> bool:
        if directroy.count('~') == 1:
            index, name = directroy.split('~')
            return index.isdigit()
        return False

    def import_sorted_zip(self, filepath: str) -> Optional[dict]:
        with zipfile.ZipFile(filepath, 'r') as zip_file:
            filepaths = sorted(zip_file.namelist())
        categories = defaultdict(list) 

        for file in filepaths:
            category, action_file = file.split("/")
            if not (self.valid_file(action_file) and self.valid_directory(category)):
                return None
            categories[category].append(file)
        for item in categories.values():
            item.sort(key= lambda x: int(x.split('~')[0]))
        return categories

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.import_settings.clear()
        
        if os.path.exists(self.filepath):
            if self.filepath.endswith(".zip"):
                AR.import_extension = ".zip"
                categories_path = self.import_sorted_zip(self.filepath)
                if categories_path is None and not self.from_operator:
                    self.report({'ERROR'}, "The selected file is not compatible")
                    return {'CANCELLED'}
                for key, item in sorted(categories_path.items(), key= lambda x: int(x[0].split('~')[0])):
                    new_category = AR.import_settings.add()
                    new_category.identifier = key
                    new_category.label = key.split('~')[1]
                    for file in item:
                        new_action = new_category.actions.add()
                        new_action.identifier = file
                        new_action.label = file.split("/")[1].split('~')[1]
                return {"FINISHED"}
            elif self.filepath.endswith(".json"):
                AR.import_extension = ".json"
                with open(self.filepath, 'r') as file:
                    data = json.loads(file.read())
                actions = data['actions']
                for category in data['categories']:
                    new_category = AR.import_settings.add()
                    new_category.identifier = category['id']
                    new_category.label = category['label']
                    for action in actions[category['start'] : category['length']]:
                        new_action = new_category.actions.add()
                        new_action.identifier = action['id']
                        new_action.label = action['label']
        if not self.from_operator:
            self.report({'ERROR'}, "You need to select a .json or .zip file")
        self.from_operator = False
        return {'CANCELLED'}
classes.append(AR_OT_global_import_settings)

class AR_OT_Export(Operator, ExportHelper):
    bl_idname = "ar.data_export"
    bl_label = "Export"
    bl_description = "Export the Action file as a ZIP"

    filter_glob: StringProperty(default= '*.json', options= {'HIDDEN'})
    filename_ext = ".json"
    filepath : StringProperty(name= "File Path", maxlen= 1024, default= "ActionRecorderButtons")

    all_categories : BoolProperty(name= "All", description= "Export all category")
    export_categories : CollectionProperty(type= properties.AR_global_export_categories)

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.global_actions)

    def execute(self, context):
        data = defaultdict(list)
        export_category_ids = set(category.id for category in self.export_categories if category.use)
        export_action_ids = []
        for category in self.export_categories:
            export_action_ids += set(action.id for action in category.actions if action.use)
            
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, 'all_categories', text= "All")
        for category in self.export_categories:
            box = layout.box()
            col = box.column()
            row = col.row()
            row.prop(category, 'show', icon="TRIA_DOWN" if category.show else "TRIA_RIGHT", text= "", emboss= False)
            row.label(text= category.label)
            row.prop(category, 'use', text= "")
            if category.show:
                col = box.column(align= False)
                for action in self.export_actions[category.start : category.start + category.length]:
                    subrow = col.row()
                    subrow.prop(action, 'use' , text= '') 
                    subrow.label(text= action.label)

    def invoke(self, context, event):
        AR = context.preferences.addons[__package__].preferences
        for category in AR.categories:
            new_category = self.export_categories.add()
            new_category.id = category.id
            new_category.label = category.label
            for action in AR.global_actions[category.start : category.start + category.length]:
                new_action = new_category.actions.add()
                new_action.id = action.id
                new_action.label = action.label
        return ExportHelper.invoke(self, context, event)
    
    def cancel(self, context):
        self.export_categories.clear()
        self.all_categories = True
classes.append(AR_OT_Export)
# endregion