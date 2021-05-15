# region Import
# external modules
import json

# blender modules
from refactor import Add
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, EnumProperty, BoolProperty, IntProperty

# relativ imports
from .. import functions as fc
from .. import ar_category
from ..preferences import AR_preferences

# endregion

classes = []

# region Operators
class AR_OT_Category_Interface(Operator):

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

    name : StringProperty(name = "Name", default="")
    area : EnumProperty(items= area_items, name= "Area", description= "Shows all available areas for the panel")
    mode : EnumProperty(items= mode_items, name= "Mode", description= "Shows all available modes for the selected area")

    def write_category_visibility(data: dict) -> None:
        with open(AR_preferences.category_visibility_path, 'w', encoding= 'utf8') as file:
            file.write(json.dumps(data, indent= 4))

    def apply_visibility(self, category_visibility: dict, visibility_options: dict, name: str) -> None:
        for area in visibility_options:
            category_visibility.setdefault('Area', {})
            category_visibility['Area'].setdefault(area, {})
            file_area = category_visibility['Area'][area]
            file_area.setdefault('categories', [])
            file_area['categories'].append(name)
            for mode in visibility_options[area]:
                file_area.setdefault('Mode', {})
                file_area['Mode'].setdefault(mode, [])
                file_area['Mode'][mode].append(name)
        self.write_category_visibility(category_visibility)

    def category_visibility_to_list(visibility_options: dict) -> list:
        l = []
        for area in visibility_options:
            for mode in visibility_options[area]:
                l.append((area, mode))
        return l

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'name')
        layout.prop(self, 'area')
        if len(self.mode_items(context)):
            layout.prop(self, 'mode')
        ops = layout.operator(AR_OT_Category_Apply_Visibility.bl_idname)
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
                ops = row.operator(AR_OT_Category_Delete_Visibility.bl_idname, text= '', icon= 'PANEL_CLOSE', emboss= False)
                ops.area = self.area
                ops.mode = self.mode

class AR_OT_Category_Add(AR_OT_Category_Interface, Operator):
    bl_idname = "ar.category_add"
    bl_label = "Add Category"

    def invoke(self, context, event):
        AR_preferences.category_visibility_data.clear()
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        new = AR.categories.add()
        name = fc.check_for_dublicates([n.name for n in AR.categories], self.name)
        new.name = name
        new.start = len(AR.Instance_Coll)
        new.length = 0
        ar_category.panles.register_unregister_category(ar_category.functions.get_panel_index(new))
        bpy.context.area.tag_redraw()
        self.apply_visibility(ar_category.functions.read_category_visbility(), AR_preferences.category_visibility_data, name)
        ar_category.functions.category_runtime_save(AR)
        return {"FINISHED"}
classes.append(AR_OT_Category_Add)

class AR_OT_Category_Edit(AR_OT_Category_Interface ,Operator):
    bl_idname = "ar.category_edit"
    bl_label = "Edit Category"
    
    category_name : StringProperty(name= "Category Name", description= "Category being edited")
    cancel_data = {}
    category_visibility = {}

    def invoke(self, context, event):
        self.cancel_data = {}
        name = self.name
        
        self.category_visibility = ar_category.functions.read_category_visbility()
        for area in self.category_visibility.get('Area', {}):
            category_visibility_area = self.category_visibility['Area'][area]
            if name in category_visibility_area.get('categories', []):
                category_visibility_area['categories'].remove(name)
                self.cancel_data[area] = []
                cancel_data_area = self.cancel_data[area]
            for mode in category_visibility_area.get('Mode', {}):
                category_visibility_mode = category_visibility_area['Mode'][mode]
                if name in category_visibility_mode:
                   category_visibility_mode.remove(name)
                   cancel_data_area.append(mode)
        AR_preferences.category_visibility_data = self.cancel_data
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        name = self.name
        self.apply_visibility(self.category_visibility, AR_preferences.category_visibility_data, name)
        ar_category.functions.category_runtime_save(AR)
        return {"FINISHED"}
classes.append(AR_OT_Category_Edit)

class AR_OT_Category_Apply_Visibility(Operator):
    bl_idname = "ar.category_apply_visibility"
    bl_label = "Apply Visibility"
    bl_description = ""
    bl_options = {"INTERNAL"}

    mode : StringProperty()
    area : StringProperty()

    def execute(self, context):
        AR_preferences.category_visibility_data.setdefault(self.area, [])
        AR_preferences.category_visibility_data[self.area].append(self.mode)
        return {"FINISHED"}
classes.append(AR_OT_Category_Apply_Visibility)

class AR_OT_Category_Delete_Visibility(Operator):
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
classes.append(AR_OT_Category_Delete_Visibility)

class AR_OT_Category_Delete(Operator):
    bl_idname = "ar.category_delete"
    bl_label = "Delete Category"
    bl_description = "Delete the selected Category"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.categories)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        categories = AR.categories
        index = ar_category.functions.get_selected_index(AR.selected_category)
        if not index is None:
            cat = categories[index]
            name = cat.name
            start = cat.start
            for i in range(start, start + cat.length):
                AR.category_action_enum.remove(len(AR.category_action_enum) - 1)
                AR.global_actions.remove(start)
            for nextcat in categories[index + 1 :]:
                nextcat.start -= cat.length
            categories.remove(index)
            ar_category.panles.unregister_category(len(categories))
            SetEnumIndex()
            for area in CatVisibility['Area']:
                if name in CatVisibility['Area'][area]: 
                    CatVisibility['Area'][area].remove(name)
            for mode in CatVisibility['Mode']:
                if name in CatVisibility['Mode'][mode]:
                    CatVisibility['Mode'][mode].remove(name)
            WriteCatVis(CatVisibility)
        bpy.context.area.tag_redraw()
        TempSaveCats()
        if AR.Autosave:
            Save()
        return {"FINISHED"}
    
    def draw(self, context):    
        AR = context.preferences.addons[__package__].preferences    
        layout = self.layout
        layout.label(text= "All Actions in this Category will be deleted", icon= 'ERROR')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
classes.append(AR_OT_Category_Delete)

class AR_OT_Category_Edit(Operator):
    bl_idname = "ar.category_edit"
    bl_label = "Edit Category"
    bl_description = "Edit the selected Category"

    @classmethod
    def poll(cls, context):
        AR = context.preferences.addons[__package__].preferences
        return len(AR.Categories)

    def execute(self, context):
        AR = context.preferences.addons[__package__].preferences
        index = None
        for cat in AR.Selected_Category:
            if cat.selected:
                index = cat.index
        if index != None:
            bpy.ops.ar.category_add('INVOKE_DEFAULT', edit= True, catName= AR.Categories[index].pn_name) 
        return {"FINISHED"}
classes.append(AR_OT_Category_Edit)
# endregion
