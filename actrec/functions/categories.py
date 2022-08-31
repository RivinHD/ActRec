# region Imports
# external modules
from typing import Optional

# blender modules
import bpy
from bpy.app.handlers import persistent

# relative imports
from . import globals, shared
from .. import shared_data
# endregion

__module__ = __package__.split(".")[0]

# region functions


def read_category_visibility(AR: bpy.types.AddonPreferences, id: str) -> Optional[list]:
    """
    get all areas and modes where the category with the given id is visible

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        id (str): id of the category

    Returns:
        Optional[list]: dict on success, None on fail
    """
    visibility = []
    category = AR.categories.get(id, None)
    if category:
        for area in category.areas:
            for mode in area.modes:
                visibility.append((area.type, mode.type))
            if len(area.modes) == 0:
                visibility.append((area.type, 'all'))
        return visibility


def category_runtime_save(AR: bpy.types.AddonPreferences, use_autosave: bool = True):
    """
     save categories to the local temp (dict) while Blender is running

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        use_autosave (bool, optional):
            include autosave to storage file (depend on AddonPreference autosave).
            Defaults to True.
    """
    shared_data.categories_temp = shared.property_to_python(AR.categories)
    if use_autosave and AR.autosave:
        globals.save(AR)


@persistent
def category_runtime_load(dummy: bpy.types.Scene = None):
    """
    load categories while Blender is running from the local temp (dict)

    Args:
        dummy (bpy.types.Scene, optional): unused. Defaults to None.
    """
    AR = bpy.context.preferences.addons[__module__].preferences
    AR.categories.clear()
    for category in shared_data.categories_temp:
        shared.add_data_to_collection(AR.categories, category)


def get_category_id(AR: bpy.types.AddonPreferences, id: str, index: int) -> str:
    """
    get category id based on id (check for existence) or index
    fallback to selected category if no match occurred

    Args:
        AR (bpy.types.AddonPreferences): Blender preferences of this addon
        id (str): id to check
        index (int): index of the category

    Returns:
        str: id of the category, fallback to selected category if not found
    """
    if AR.categories.find(id) == -1:
        if index >= 0 and len(AR.categories) > index:
            return AR.categories[index].id
        else:
            return AR.selected_category
    else:
        return id
# endregion
