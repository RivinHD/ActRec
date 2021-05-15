# region Imports
# external modules
import json
import os

# blender modules
import bpy

# relativ imports
from .. import ar_category
from ..preferences import AR_preferences

# endregion 

# region functions
def get_panel_index(categorie) -> int: #Get Index of a Category
    AR = bpy.context.preferences.addons[__package__].preferences
    return AR.categories.find(categorie.name)

def read_category_visbility() -> dict:
    path = AR_preferences.category_visibility_path
    if not os.path.exists(path):
        with open(path, 'w', encoding= 'utf-8') as file:
            file.write("{}")
    with open(path, 'r', encoding= 'utf-8') as file:
       return json.loads(file.read()) 

def category_runtime_save(AR) -> None:
    TempSaveCats()
    if AR.Autosave:
        Save()

def get_selected_index(selections):
    for sel in selections:
        if sel.selected:
            return sel.index
    return 0

# endregion
