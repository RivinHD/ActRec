# region Imports
# external modules
import os

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy_extras.io_utils import ImportHelper

# relative imports
from .. import functions
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
                functions.category_runtime_save(AR)
                if AR.autosave:
                    Save()
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
    AddNewCategory : BoolProperty(default= False)
    mode : EnumProperty(name= 'Mode', items= [("add","Add",""),("overwrite", "Overwrite", "")])

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        ar_categories = AR.Categories
        if self.filepath.endswith(".zip"):
            if self.AddNewCategory:
                dirfileslist, sorteddirlist = ImportSortedZip(self.filepath)
                with zipfile.ZipFile(self.filepath, 'r') as zip_out:
                    mycat = ar_categories.add()
                    name = CheckForDublicates([n.pn_name for n in ar_categories], self.Category)
                    mycat.name = name
                    mycat.pn_name = name
                    mycat.Instance_Start = len(AR.Instance_Coll)
                    RegisterUnregister_Category(ar_category.functions.get_panel_index(mycat))
                    for dirs in dirfileslist:
                        for btn_file in dirs:
                            name_icon = os.path.splitext(os.path.basename(btn_file))[0]
                            name = "".join(name_icon.split("~")[1:-1])
                            inst = AR.Instance_Coll.add()
                            inst.name = CheckForDublicates([AR.Instance_Coll[i].name for i in range(mycat.Instance_Start, mycat.Instance_Start + mycat.Instance_length)], name)
                            inst.icon = check_icon(name_icon.split("~")[-1])
                            for line in zip_out.read(btn_file).decode("utf-8").splitlines():
                                cmd = inst.commands.add()
                                cmd.name = line
                            new_e = AR.ar_enum.add()
                            e_index = len(AR.ar_enum) - 1
                            new_e.name = str(e_index)
                            new_e.Index = e_index
                            mycat.Instance_length += 1
            else:
                if not len(AR.Importsettings):
                    if bpy.ops.ar.data_import_options('EXEC_DEFAULT', filepath= self.filepath, fromoperator= True) == {'CANCELLED'}:
                        self.report({'ERROR'}, "The selected file is not compatible")
                        return {'CANCELLED'}
                for icat in AR.Importsettings:
                    Index = -1
                    mycat = None
                    if icat.enum == 'append':
                        Index = AR.Categories.find(icat.cat_name)
                    if Index == -1:
                        mycat = ar_categories.add()
                        name = icat.cat_name
                        name = CheckForDublicates([n.pn_name for n in ar_categories], name)
                        mycat.name = name
                        mycat.pn_name = name
                        mycat.Instance_Start = len(AR.Instance_Coll)
                        RegisterUnregister_Category(ar_category.functions.get_panel_index(mycat))
                    else:
                        mycat = ar_categories[Index]
                        for btn in icat.Buttons:
                            if btn.enum == 'overwrite':
                                for i in range(mycat.Instance_Start, mycat.Instance_Start + mycat.Instance_length):
                                    inst = AR.Instance_Coll[i]
                                    if btn.btn_name == inst.name:
                                        inst.name = btn.btn_name
                                        inst.icon = check_icon(btn.icon)
                                        inst.commands.clear()
                                        for cmd in btn.commands.splitlines():
                                            new = inst.commands.add()
                                            new.name = cmd
                                        break
                                else:
                                    btn.enum = 'add'

                    for btn in icat.Buttons:
                        if btn.enum == 'overwrite':
                            continue
                        inserti = mycat.Instance_Start + mycat.Instance_length
                        name = btn.btn_name
                        icon = btn.icon
                        data = {"name": CheckForDublicates([AR.Instance_Coll[i].name for i in range(mycat.Instance_Start, mycat.Instance_Start + mycat.Instance_length)], name),
                                "command": btn.commands.splitlines(),
                                "icon": icon}
                        Inst_Coll_Insert(inserti, data, AR.Instance_Coll)
                        new_e = AR.ar_enum.add()
                        e_index = len(AR.ar_enum) - 1
                        new_e.name = str(e_index)
                        new_e.Index = e_index
                        mycat.Instance_length += 1
                        if Index != -1:
                            for cat in ar_categories[Index + 1:] :
                                cat.Instance_Start += 1
            set_enum_index()()
            if AR.Autosave:
                Save()
        else:
            self.report({'ERROR'}, "{ " + self.filepath + " } Select a .zip file")
        AR = context.preferences.addons[__package__].preferences
        AR.Importsettings.clear()
        TempSaveCats()
        return {"FINISHED"}
    
    def draw(self, context):
        AR = context.preferences.addons[__package__].preferences
        layout = self.layout
        layout.prop(self, 'AddNewCategory', text= "Append to new Category")
        if self.AddNewCategory:
            layout.prop(self, 'Category', text= "Name")
        else:
            layout.operator(AR_OT_ImportLoadSettings.bl_idname, text= "Load Importsettings").filepath = self.filepath
            for cat in AR.Importsettings:
                box = layout.box()
                col = box.column()
                row = col.row()
                if cat.show:
                    row.prop(cat, 'show', icon="TRIA_DOWN", text= "", emboss= False)
                else:
                    row.prop(cat, 'show', icon="TRIA_RIGHT", text= "", emboss= False)
                row.label(text= cat.cat_name)
                row.prop(cat, 'enum', text= "")
                if cat.show:
                    col = box.column()
                    for btn in cat.Buttons:
                        row = col.row()
                        row.label(text= btn.btn_name)
                        if cat.enum == 'append':
                            row.prop(btn, 'enum', text= "")
        
    def cancel(self, context):
        AR = context.preferences.addons[__package__].preferences
        AR.Importsettings.clear()
classes.append(AR_OT_global_import)

class AR_OT_global_import_settings(Operator):
    bl_idname = "ar.global_import_settings"
    bl_label = "Load Importsettings"
    bl_description = "Load the select the file to change the importsettings"

    filepath : StringProperty()
    fromoperator : BoolProperty()

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        if os.path.exists(self.filepath) and self.filepath.endswith(".zip"):
            dirfileslist, sorteddirlist = ImportSortedZip(self.filepath)
            if dirfileslist is None:
                if not self.fromoperator:
                    self.report({'ERROR'}, "The selected file is not compatible")
                self.fromoperator = False
                return {'CANCELLED'}
            with zipfile.ZipFile(self.filepath, 'r') as zip_out:
                AR.Importsettings.clear()
                for i in range(len(sorteddirlist)):
                    cat = AR.Importsettings.add()
                    cat.cat_name = "".join(sorteddirlist[i].split("~")[1:])
                    for dir_file in dirfileslist[i]:
                        btn = cat.Buttons.add()
                        name_icon = os.path.splitext(os.path.basename(dir_file))[0]
                        btn.btn_name = "".join(name_icon.split("~")[1:-1])
                        btn.icon = name_icon.split("~")[-1]
                        btn.commands = zip_out.read(dir_file).decode("utf-8")
                return {"FINISHED"}
        else:
            self.report({'ERROR'}, "You need to select a .zip file")
            return {'CANCELLED'}
classes.append(AR_OT_global_import_settings)
# endregion