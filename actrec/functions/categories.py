# region Imports
# external modules
import json
import os
from collections import defaultdict

# blender modules
import bpy

# endregion

# region functions
def get_panel_index(categorie) -> int: #Get Index of a Category
    AR = bpy.context.preferences.addons[__package__].preferences
    return AR.categories.find(categorie.id)

def get_selected_index(selections) -> int:
    for sel in selections:
        if sel.selected:
            return sel.index
    return 0

def read_category_visbility() -> dict:
    path = AR_preferences.category_visibility_path
    if not os.path.exists(path):
        with open(path, 'w', encoding= 'utf-8') as file:
            file.write("{}")
    with open(path, 'r', encoding= 'utf-8') as file:
       return defaultdict(lambda: {"categories": [], "Mode": lambda: defaultdict(list)}, json.loads(file.read()))
    
def write_category_visibility(data: dict) -> None:
    with open(AR_preferences.category_visibility_path, 'w', encoding= 'utf-8') as file:
        file.write(json.dumps(data, indent= 4))

def category_runtime_save(AR) -> None:
    TempSaveCats()
    if AR.Autosave:
        Save()

def adjust_categories(categories, categorie, change: int) -> None:
    for adjust_categorie in categories:
        if adjust_categorie.start > categorie.start:
            adjust_categorie.start += change
# endregion