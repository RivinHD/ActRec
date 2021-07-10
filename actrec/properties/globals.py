# region Imports
# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, IntProperty, StringProperty, CollectionProperty, EnumProperty

# relative Imports
from . import shared
# endregion

classes = []

# region PropertyGroups
class AR_global_actions_enum(PropertyGroup):
    index : IntProperty()
classes.append(AR_global_actions_enum)

class AR_global_import_action(PropertyGroup):
    def get_use(self):
        return self.get("use", True) and self.get('category.use', True)
    def set_use(self, value):
        if self.get('category.use', True):
            self['use'] = value
    
    label : StringProperty()
    identifier : StringProperty()
    use : BoolProperty(default= True, name= "Import Action", description= "Decide whether to import the action", get= get_use, set= set_use)
classes.append(AR_global_import_action)

class AR_global_import_category(PropertyGroup):
    def get_use(self):
        return self.get("use", True)
    def set_use(self, value):
        self['use'] = value
        for action in self.actions:
            action['category.use'] = value

    label : StringProperty()
    identifier : StringProperty()
    actions : CollectionProperty(type= AR_global_import_action)
    mode : EnumProperty(items= [("new", "New", "Create a new Category"),("append", "Append", "Append to an existing Category")], name= "Import Mode")
    show : BoolProperty(default= True)
    use : BoolProperty(default= True, name= "Import Category", description= "Decide whether to import the category", get= get_use, set= set_use)
classes.append(AR_global_import_category)

class AR_global_export_action(shared.id_system, PropertyGroup):
    def get_use(self):
        return self.get("use", True) and self.get('category.use', True)
    def set_use(self, value):
        if self.get('category.use', True):
            self['use'] = value
    
    label : StringProperty()
    use : BoolProperty(default= True, name= "Import Action", description= "Decide whether to import the action", get= get_use, set= set_use)
classes.append(AR_global_export_action)

class AR_global_export_categories(shared.id_system, PropertyGroup):
    def get_use(self):
        return self.get("use", True)
    def set_use(self, value):
        self['use'] = value
        for action in self.actions:
            action['category.use'] = value

    label : StringProperty()
    actions : CollectionProperty(type= AR_global_import_action)
    show : BoolProperty(default= True)
    use : BoolProperty(default= True, name= "Export Category", description= "Decide whether to export the category", get= get_use, set= set_use)
classes.append(AR_global_export_categories)
# endregion