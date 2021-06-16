# region Imports
# external modules
from collections import defaultdict

# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, IntProperty, StringProperty

# relative imports
from . import shared
from .. import functions 
# endregion

classes = []

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
        index = functions.get_panel_index(self)
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