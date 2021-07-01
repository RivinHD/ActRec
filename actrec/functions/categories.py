# region Imports
# external modules
import json
import os
from typing import Optional

# blender modules
import bpy

# relative imports
from . import globals
from .. import properties
# endregion

# region functions
def get_storage_data(AR) -> dict:
    path = AR.storage_path
    if not os.path.exists(path):
        with open(path, 'w', encoding= 'utf-8') as file:
            file.write("{}")
    with open(path, 'r', encoding= 'utf-8') as file:
        data = json.loads(file.read())
    return data

def read_category_visbility(AR, category_id) -> Optional[list]:
    """return None on Fail, dict on Successes"""
    visibility = []
    data = get_storage_data(AR)
    for category in data['categories']:
        if category['id'] == category_id:
            for area in category['areas']:
                for mode in area['modes']:
                    visibility.append((area['type'], mode['type']))
                if len(area['modes']) == 0:
                    visibility.append((area['type'], None))
            return visibility

def temp_save_categories(AR):
    data = properties.data_manager.categories_temp


def category_runtime_save(AR) -> None:
    """includes autosave"""
    temp_save_categories(AR)
    if AR.autosave:
        globals.save(AR)

def adjust_categories(categories, category, change: int) -> None:
    """adjust the 'start'-property of the categories after the 'category' by the 'change' value"""
    for adjust_categorie in categories:
        if adjust_categorie.start > category.start:
            adjust_categorie.start += change

def swap_categories(category_1, category_2) -> None:
    category_1.id, category_2.id = category_2.id, category_1.id
    category_1.label, category_2.label = category_2.label, category_1.label
    category_1.selected, category_2.selected = category_2.selected, category_1.selected
    category_1.start, category_2.start = category_2.start, category_1.start
    category_1.length, category_2.length = category_2.length, category_1.length

# endregion