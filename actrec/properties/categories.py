# region Imports
# external modules
from collections import defaultdict

# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, IntProperty, StringProperty, CollectionProperty

# relative imports
from . import shared
# endregion

classes = []

# region PropertyGroups
class AR_categories_modes(PropertyGroup):
    def get_name(self):
        self['name'] = self.type
        return self['name']

    name : StringProperty(get= get_name)
    type : StringProperty()
classes.append(AR_categories_modes)

class AR_categories_areas(PropertyGroup):
    def get_name(self):
        self['name'] = self.type
        return self['name']

    name : StringProperty(get= get_name)
    type : StringProperty()
    modes : CollectionProperty(type= AR_categories_modes)
classes.append(AR_categories_areas)

class AR_categories(shared.id_system, PropertyGroup):
    def get_selected(self) -> bool:
        return self.get("selected", False)
    def set_selected(self, value: bool) -> None:
        AR = bpy.context.preferences.addons[__package__].preferences
        selected_id = AR.get("categories.selected_id", None)
        if value:
            if selected_id != None:
                AR.categories[selected_id].selected = False
            AR["categories.selected_id"] = self.id
            self['selected'] = value
        elif selected_id != self.id:
            self['selected'] = value

    label : StringProperty()
    selected : BoolProperty(description= 'Select this Category', name= 'Select', get= get_selected, set= set_selected)
    start : IntProperty(default= 0)
    length : IntProperty(default= 0)
    areas : CollectionProperty(type= AR_categories_areas)
classes.append(AR_categories)
# endregion
