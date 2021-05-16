# region Import
# external modules
import os

# blender modules
import bpy
from bpy.types import PropertyGroup, AddonPreferences
from bpy.props import IntProperty, CollectionProperty, BoolProperty, StringProperty

# relativ imports
from .. import ar_category
from .. import log
from ..preferences import AR_preferences
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


class AR_categories(PropertyGroup):

    def get_selected(self) -> bool:
        return self.get("selected", False)
    def set_selected(self, value: bool) -> None:
        AR = bpy.context.preferences.addons[__package__].preferences
        selected_index = AR.get("categories_props.selected_index", None)
        index = ar_category.functions.get_panel_index(self)
        if value:
            if selected_index != None:
                AR.categories[selected_index] = False
            AR["categories_props.selected_index"] = index
            self['selected'] = value
        elif selected_index != index:
            self['selected'] = value

    name : StringProperty()
    selected : BoolProperty(default= False, get= get_selected, set= set_selected)
    start : IntProperty(default= 0)
    length : IntProperty(default= 0)
classes.append(AR_categories)
# endregion

# region preferences
class Preferences(AddonPreferences):
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
                    transferfolders.append(str(ar_category.functions.get_panel_index(cat)) + "~" + cat.pn_name)
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
    category_visibility_data = {}
# endregion

# region Registration
def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister() -> None:
    for cls in classes:
        bpy.utils.unregister_class(cls)
# endregion
