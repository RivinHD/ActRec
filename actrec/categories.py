# region Imports
# external modules
import json
import os
from collections import defaultdict
from contextlib import suppress

# blender modules
import bpy
from bpy.types import Operator, PropertyGroup, Panel
from bpy.props import StringProperty, EnumProperty, IntProperty, CollectionProperty, BoolProperty, StringProperty

# relativ imports
from .preferences import AR_preferences
from . import globals, log, shared
# endregion 

classes = []

# region functions
def get_panel_index(categorie) -> int: #Get Index of a Category
    AR = bpy.context.preferences.addons[__package__].preferences
    return AR.categories.find(categorie.id)

def read_category_visbility() -> dict:
    path = AR_preferences.category_visibility_path
    if not os.path.exists(path):
        with open(path, 'w', encoding= 'utf-8') as file:
            file.write("{}")
    with open(path, 'r', encoding= 'utf-8') as file:
       return defaultdict(lambda: {"categories": [], "Mode": lambda: defaultdict(list)}, json.loads(file.read()))
    
def write_category_visibility(data: dict) -> None:
    with open(AR_preferences.category_visibility_path, 'w', encoding= 'utf8') as file:
        file.write(json.dumps(data, indent= 4))

def category_runtime_save(AR) -> None:
    TempSaveCats()
    if AR.Autosave:
        Save()

def get_selected_index(selections) -> int:
    for sel in selections:
        if sel.selected:
            return sel.index
    return 0

def adjust_categories(categories, categorie, change: int) -> None:
    for adjust_categorie in categories:
        if adjust_categorie.start > categorie.start:
            adjust_categorie.start += change
# endregion

# region Operators
class AR_OT_category_interface(Operator):

    """import bpy
        try:
            bpy.context.area.ui_type = ""
        except TypeError as err:
            enum_items = eval(str(err).split('enum "" not found in ')[1])
            current_ui_type = bpy.context.area.ui_type
            my_dict = {}
            for item in enum_items:
                bpy.context.area.ui_type = item
                my_dict[item] = bpy.context.area.type
            print(my_dict)
            bpy.context.area.ui_type = current_ui_type
    """ # code to get areas_to_spaces
    # don't use it, because it's based on an error message and it doesn't contains enough data
    areas_to_spaces = {
        'VIEW_3D': 'VIEW_3D', 
        'IMAGE_EDITOR': 'IMAGE_EDITOR', 
        'UV': 'IMAGE_EDITOR', 
        'CompositorNodeTree': 'NODE_EDITOR', 
        'TextureNodeTree': 'NODE_EDITOR', 
        'GeometryNodeTree': 'NODE_EDITOR', 
        'ShaderNodeTree': 'NODE_EDITOR', 
        'SEQUENCE_EDITOR': 'SEQUENCE_EDITOR', 
        'CLIP_EDITOR': 'CLIP_EDITOR', 
        'DOPESHEET': 'DOPESHEET_EDITOR', 
        'TIMELINE': 'DOPESHEET_EDITOR', 
        'FCURVES': 'GRAPH_EDITOR', 
        'DRIVERS': 'GRAPH_EDITOR', 
        'NLA_EDITOR': 'NLA_EDITOR', 
        'TEXT_EDITOR': 'TEXT_EDITOR', 
        'CONSOLE': 'CONSOLE', 
        'INFO': 'INFO', 
        'OUTLINER': 'OUTLINER', 
        'PROPERTIES': 'PROPERTIES', 
        'FILES': 'FILE_BROWSER', 
        'PREFERENCES': 'PREFERENCES'
    }

    modes = {
        'EMPTY': [],
        'VIEW_3D': [(item.identifier, item.name, item.description, item.icon, item.value) for item in bpy.types.Context.bl_rna.properties['mode'].enum_items], 
        'IMAGE_EDITOR': [(item.identifier, item.name, item.description, item.icon, item.value) for item in bpy.types.SpaceImageEditor.bl_rna.properties['ui_mode'].enum_items], 
        'NODE_EDITOR': [(item.identifier, item.name, item.description, item.icon, item.value) for item in  bpy.types.SpaceNodeEditor.bl_rna.properties['texture_type'].enum_items], 
        'SEQUENCE_EDITOR': [(item.identifier, item.name, item.description, item.icon, item.value) for item in bpy.types.SpaceSequenceEditor.bl_rna.properties['view_type'].enum_items], 
        'CLIP_EDITOR': [(item.identifier, item.name, item.description, item.icon, item.value) for item in bpy.types.SpaceClipEditor.bl_rna.properties['mode'].enum_items], 
        'DOPESHEET_EDITOR': [(item.identifier, item.name, item.description, item.icon, item.value) for item in bpy.types.SpaceDopeSheetEditor.bl_rna.properties['ui_mode'].enum_items], 
        'GRAPH_EDITOR': [], 
        'NLA_EDITOR': [], 
        'TEXT_EDITOR': [], 
        'CONSOLE': [], 
        'INFO': [],  
        'TOPBAR': [], 
        'STATUSBAR': [],  
        'OUTLINER': [(item.identifier, item.name, item.description, item.icon, item.value) for item in bpy.types.Context.bl_rna.properties['mode'].enum_items], 
        'PROPERTIES': [(item.identifier, item.name, item.description, item.icon, item.value) for item in bpy.types.Context.bl_rna.properties['mode'].enum_items], 
        'FILE_BROWSER': [(item.identifier, item.name, item.description, item.icon, item.value) for item in bpy.types.Context.bl_rna.properties['mode'].enum_items], 
        'PREFERENCES': [(item.identifier, item.name, item.description, item.icon, item.value) for item in bpy.types.Context.bl_rna.properties['mode'].enum_items]
    }

    area_items = [ # (identifier, name, description, icon, value)
        ('VIEW_3D', '3D Viewport', '', 'VIEW3D', 0),
        ('IMAGE_EDITOR', 'Image Editor', '', 'IMAGE', 1),
        ('UV', 'UV Editor', '', 'UV', 2),
        ('CompositorNodeTree', 'Compositor', '', 'NODE_COMPOSITING', 3),
        ('TextureNodeTree', 'Texture Node Editor', '', 'NODE_TEXTURE', 4),
        ('GeometryNodeTree', 'Geomerty Node Editor', '', 'NODETREE', 5),
        ('ShaderNodeTree', 'Shader Editor', '', 'NODE_MATERIAL', 6),
        ('SEQUENCE_EDITOR', 'Video Sequencer', '', 'SEQUENCE', 7),
        ('CLIP_EDITOR', 'Movie Clip Editor', '', 'TRACKER', 8),
        ('DOPESHEET', 'Dope Sheet', '', 'ACTION', 9),
        ('TIMELINE', 'Timeline', '', 'TIME', 10),
        ('FCURVES', 'Graph Editor', '', 'GRAPH', 11),
        ('DRIVERS', 'Drivers', '', 'DRIVER', 12),
        ('NLA_EDITOR', 'Nonlinear Animation', '', 'NLA', 13),
        ('TEXT_EDITOR', 'Text Editor', '', 'TEXT', 14),
        ('CONSOLE', 'Python Console', '', 'CONSOLE', 15),
        ('INFO', 'Info', '', 'INFO', 16),
        ('OUTLINER', 'Outliner', '', 'OUTLINER', 17),
        ('PROPERTIES', 'Properties', '', 'PROPERTIES', 18),
        ('FILES', 'File Browser', '', 'FILEBROWSER', 19),
        ('PREFERENCES', 'Preferneces', '', 'PREFERENCES', 20)
    ]
    def mode_items(self, context) -> list:
        return self.modes.get(self.areas_to_spaces[self.area], [])

    label : StringProperty(name = "Category Label", default="")
    area : EnumProperty(items= area_items, name= "Area", description= "Shows all available areas for the panel")
    mode : EnumProperty(items= mode_items, name= "Mode", description= "Shows all available modes for the selected area")

    def apply_visibility(self, category_visibility: dict, visibility_options: dict, label: str) -> None:
        for area in visibility_options:
            file_area = category_visibility[area]
            file_area['categories'].append(label)
            for mode in visibility_options[area]:
                file_area['Mode'][mode].append(label)
        write_category_visibility(category_visibility)

    def category_visibility_to_list(visibility_options: dict) -> list:
        l = []
        for area in visibility_options:
            for mode in visibility_options[area]:
                l.append((area, mode))
        return l

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'label')
        layout.prop(self, 'area')
        if len(self.mode_items(context)):
            layout.prop(self, 'mode')
        ops = layout.operator(AR_OT_category_apply_visibility.bl_idname)
        ops.area = self.area
        ops.mode = self.mode
        visibility_options = AR_preferences.category_visibility_data
        if len(visibility_options) > 0:
            box = layout.box()
            row = box.row()
            row.label(text= "Area")
            row.label(text= "Mode")
            row.label(icon= 'BLANK1')
            for visbility in self.category_visibility_to_list(visibility_options):
                row = box.row()
                row.label(text= visbility[0])
                row.label(text= visbility[1])
                ops = row.operator(AR_OT_category_delete_visibility.bl_idname, text= '', icon= 'PANEL_CLOSE', emboss= False)
                ops.area = self.area
                ops.mode = self.mode

class AR_OT_category_add(AR_OT_category_interface, Operator):
    bl_idname = "ar.category_add"
    bl_label = "Add Category"

    def invoke(self, context, event):
        AR_preferences.category_visibility_data.clear()
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        new = AR.categories.add()
        label = shared.check_for_dublicates([n.label for n in AR.categories], self.label)
        new.label = label
        new.start = len(AR.Instance_Coll)
        new.length = 0
        register_unregister_category(get_panel_index(new))
        bpy.context.area.tag_redraw()
        self.apply_visibility(read_category_visbility(), AR_preferences.category_visibility_data, label)
        category_runtime_save(AR)
        return {"FINISHED"}
classes.append(AR_OT_category_add)

class AR_OT_category_edit(AR_OT_category_interface ,Operator):
    bl_idname = "ar.category_edit"
    bl_label = "Edit Category"
    bl_description = "Edit the selected Category"

    cancel_data = {}
    category_visibility = {}

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.Categories)

    def invoke(self, context, event):
        self.cancel_data = defaultdict(list)
        label = self.label
        
        self.category_visibility = read_category_visbility()
        for area in self.category_visibility:
            category_visibility_area = self.category_visibility[area]
            if label in category_visibility_area.get('categories', []):
                category_visibility_area['categories'].remove(label)
                self.cancel_data[area] = []
                cancel_data_area = self.cancel_data[area]
            for mode in category_visibility_area.get('Mode', {}):
                category_visibility_mode = category_visibility_area['Mode'][mode]
                if label in category_visibility_mode:
                   category_visibility_mode.remove(label)
                   cancel_data_area.append(mode)
        AR_preferences.category_visibility_data = self.cancel_data
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        self.apply_visibility(self.category_visibility, AR_preferences.category_visibility_data, self.label)
        category_runtime_save(AR)
        return {"FINISHED"}
classes.append(AR_OT_category_edit)

class AR_OT_category_apply_visibility(Operator):
    bl_idname = "ar.category_apply_visibility"
    bl_label = "Apply Visibility"
    bl_description = ""
    bl_options = {"INTERNAL"}

    mode : StringProperty()
    area : StringProperty()

    def execute(self, context):
        AR_preferences.category_visibility_data[self.area].append(self.mode)
        return {"FINISHED"}
classes.append(AR_OT_category_apply_visibility)

class AR_OT_category_delete_visibility(Operator):
    bl_idname = "ar.category_delete_visibility"
    bl_label = "Delete Visibility"
    bl_description = ""
    bl_options = {"INTERNAL"}

    mode : StringProperty()
    area : StringProperty()

    def execute(self, context):
        area = AR_preferences.category_visibility_data.get(self.area, None)
        if isinstance(area, list) and self.mode in area:
            AR_preferences.category_visibility_data[area].remove(self.mode)
            if len(AR_preferences.category_visibility_data[area]) == 0:
                AR_preferences.category_visibility_data.pop(area)
        return {"FINISHED"}
classes.append(AR_OT_category_delete_visibility)

class AR_OT_category_delete(Operator):
    bl_idname = "ar.category_delete"
    bl_label = "Delete Category"
    bl_description = "Delete the selected Category"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.categories)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        categories = AR.categories
        index = get_selected_index(AR.selected_category)
        if not index is None:
            categorie = categories[index]
            label = categorie.label
            start = categorie.start
            for i in range(start, start + categorie.length):
                AR.category_action_enum.remove(len(AR.category_action_enum) - 1)
                AR.global_actions.remove(start)
            adjust_categories(categories, categorie, -categorie.length)
            categories.remove(index)
            unregister_category(len(categories))
            globals.functions.set_enum_index()
            category_visibility = read_category_visbility()
            for area in category_visibility.get('Area', {}):
                if label in category_visibility['Area'][area].get('categories', []): 
                    category_visibility['Area'][area]['categories'].remove(label)
                for mode in category_visibility['Area'].get('Mode', {}):
                    if label in category_visibility['Mode'][mode]:
                        category_visibility['Mode'][mode].remove(label)
            write_category_visibility(category_visibility)
        bpy.context.area.tag_redraw()
        categories .functions.category_runtime_save(AR)
        if AR.Autosave:
            Save()
        return {"FINISHED"}
    
    def draw(self, context):    
        AR = context.preferences.addons[__package__].preferences    
        layout = self.layout
        layout.label(text= "All Actions in this Category will be deleted", icon= 'ERROR')
classes.append(AR_OT_category_delete)
# endregion

# region Panels
def register_categories(): #Register all Categories
    for i in range(catlength[0]):
        register_category(i)

def register_category(index):
    register_unregister_category(index)

def unregister_category(index):
    register_unregister_category(index, False)

def register_unregister_category(index, register = True): #Register/Unregister one Category
    for spaceType in AR_preferences.space_types:
        class AR_PT_category(Panel):
            bl_space_type = spaceType
            bl_region_type = 'UI'
            bl_category = 'Action Recorder'
            bl_label = ' '
            bl_idname = "AR_PT_category_%s_%s" %(index, spaceType)
            bl_parent_id = "AR_PT_Global_%s" % spaceType
            bl_order = index + 1

            @classmethod
            def poll(self, context):
                AR = context.preferences.addons[__package__].preferences
                index = int(self.bl_idname.split("_")[3])
                if len(AR.categories) <= index:
                    Load()
                category = AR.categories[index]
                return showCategory(category.label, context)

            def draw_header(self, context):
                AR = context.preferences.addons[__package__].preferences
                index = int(self.bl_idname.split("_")[3])
                category = AR.Categories[index]
                layout = self.layout
                row = layout.row()
                row.prop(AR.Selected_Category[index], 'selected', text= '', icon= 'LAYER_ACTIVE' if AR.Selected_Category[index].selected else 'LAYER_USED', emboss= False)
                row.label(text= category.label)

            def draw(self, context):
                AR = context.preferences.addons[__package__].preferences
                scene = context.scene
                index = int(self.bl_idname.split("_")[3])
                category = AR.Categories[index]
                layout = self.layout
                col = layout.column()
                for i in range(category.Instance_Start, category.Instance_Start + category.Instance_length):
                    globals.draw_actions(col, AR, i)
        AR_PT_category.__name__ = "AR_PT_category_%s_%s" %(index, spaceType)
        if register:
            bpy.utils.register_class(AR_PT_category)
            classes.append(AR_PT_category)
        else:
            with suppress(Exception):
                panel = eval("bpy.types.%s" %AR_PT_category.__name__)
                bpy.utils.unregister_class(panel)
                classes.remove(panel)
    AR = bpy.context.preferences.addons[__package__].preferences
    if register:
        new = AR.selected_category.add()
        new.index = index
    else:
        AR.selected_category.remove(len(AR.Selected_Category) - 1)
    if get_selected_index(AR.selected_category) is None and len(AR.selected_category):
        AR.selected_category[0].selected = True
# endregion

# region PropertyGroups
class AR_selected_category(PropertyGroup):
    def get_selected(self) -> bool:
        return self.get("selected", False)
    def set_selected(self, value: bool) -> None:
        AR = bpy.context.preferences.addons[__package__].preferences
        selected_index = AR.get("selected_category.selected_index", None)
        if value:
            if selected_index != None:
                AR.selected_category[selected_index] = False
            AR["selected_category.selected_index"] = self.index
            self['selected'] = value
        elif selected_index != self.index:
            self['selected'] = value

    selected : BoolProperty(description= 'Select this Category', name= 'Select', get= get_selected, set= set_selected)
    index : IntProperty()
classes.append(AR_selected_category)

class AR_categories(shared.id_system, PropertyGroup):
    def get_selected(self) -> bool:
        return self.get("selected", False)
    def set_selected(self, value: bool) -> None:
        AR = bpy.context.preferences.addons[__package__].preferences
        selected_index = AR.get("categories_props.selected_index", None)
        index = get_panel_index(self)
        if value:
            if selected_index != None:
                AR.categories[selected_index] = False
            AR["categories_props.selected_index"] = index
            self['selected'] = value
        elif selected_index != index:
            self['selected'] = value

    label : StringProperty()
    selected : BoolProperty(default= False, get= get_selected, set= set_selected)
    start : IntProperty(default= 0)
    length : IntProperty(default= 0)
classes.append(AR_categories)
# endregion

# region preferences
class preferences:
    def get_storage_path(self) -> str:
        origin_path = self.get('storage_path', 'Fallback')
        if os.path.exists(origin_path):
            return self['storage_path']
        else:
            path = os.path.join(AR_preferences.addon_directory, "Storage")
            if origin_path != 'Fallback':
                log.logger.error("ActRec ERROR: Storage Path \"" + origin_path +"\" don't exist, fallback to " + path)
            self['storage_path'] = path
            return path
    def set_storage_path(self, origin_path) -> str:
        if origin_path != os.path.join(AR_preferences.addon_directory, "Storage"):
            main_version = ".".join(bpy.app.version_string.split(".")[:2])
            path = os.path.join(origin_path, main_version)
            if not (os.path.exists(path) and os.path.isdir(path)):
                os.mkdir(path)
                transferfolders = []
                for cat in self.Categories:
                    transferfolders.append(str(get_panel_index(cat)) + "~" + cat.pn_name)
                for folder in os.listdir(origin_path):
                    if folder in transferfolders:
                        os.rename(os.path.join(origin_path, folder), os.path.join(path, folder))
            self['storage_path'] = origin_path
            self.exact_storage_path = path
        else:
            self['storage_path'] = origin_path
            self.exact_storage_path = origin_path
    
    storage_path : StringProperty(name= "Stroage Path", description= "The Path to the Storage for the saved Categories", default= os.path.join(os.path.dirname(__file__), "Storage"), get=get_storage_path, set=set_storage_path)
    exact_storage_path : StringProperty(description="Is the full path to the Storage Folder (includes the Version)[hidden]", default= os.path.join(os.path.dirname(__file__), "Storage"))

    categories : CollectionProperty(type= AR_categories)
    selected_category : CollectionProperty(type= AR_selected_category)
    show_all_categories : BoolProperty(name= "Show All Categories", default= False)

    AR = bpy.context.preferences.addons[__package__].preferences
    category_visibility_path = os.path.join(AR.exact_storage_path, "Category_Visibility") # set the category visibility path
    category_visibility_data = defaultdict(list)
# endregion

# region Registration 
def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
# endregion 
