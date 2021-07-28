# region Imports
# external modules
from typing import Union
from contextlib import suppress
from collections import defaultdict
# endregion

# region functions
def check_for_dublicates(l: list, name: str, num = 1) -> str: #Check for name duplicates and append .001, .002 etc.
    while name in l:
        name = "{}.{0:03d}".format(".".join(name.split(".")[:-1]), num)
        num += 1
    return name

def property_to_python(property, exclude: list = []):
    if hasattr(property, 'id_data'):
        id_property = property.id_data
        if property == id_property:
            return property
        class_name = property.__class__.__name__
        if class_name.startswith('bpy_prop_collection'):
            return  [property_to_python(item, exclude) for item in property] # ColllectionProperty
        elif class_name.startswith('bpy_prop_array'):
            return list(property)
        else:
            data = {} # PointerProperty
            main_exclude = []
            sub_exclude = defaultdict(list)
            for x in exclude:
                prop = x.split(".")
                main_exclude.append(prop[0])
                if len(prop) > 1:
                    sub_exclude[prop[0]].append(".".join(prop[1:]))
            main_exclude = set(main_exclude)
            for attr in property.bl_rna.properties[1:]:
                identifier = attr.identifier
                if identifier not in main_exclude:
                    data[identifier] = property_to_python(getattr(property, identifier), sub_exclude.get(identifier, []))
            return data
    return property

def apply_data_to_item(item, data, key = "") -> None:
    if isinstance(data, list):
        for element in data:
            apply_data_to_item(item, element)
    elif isinstance(data, dict):
        for key, value in data.items():
            apply_data_to_item(item, value, key)
    elif hasattr(item, key):
        with suppress(AttributeError): # catch Exception from read-only property
            setattr(item, key, data)

def add_data_to_collection(collection, data: dict) -> None:
    new_item = collection.add()
    apply_data_to_item(new_item, data)
                
def insert_to_collection(collection, index: int, data: dict) -> None:
    add_data_to_collection(collection, data)
    collection.move(len(collection) - 1, index)

def swap_collection_items(collection, index_1: int, index_2: int) -> None:
    if index_1 == index_2:
        return
    if index_1 < index_2:
        index_1, index_2 = index_2, index_1
    collection.move(index_1, index_2)
    collection.move(index_2 + 1, index_1)

def get_name_of_command(command: str) -> Union[None, str, True]:
    if command.startswith("bpy.ops"):
        try:
            return eval("%s.get_rna_type().name" %command.split("(")[0])
        except:
            return command
    elif command.startswith('bpy.data.window_managers["WinMan"].(null)'):
        return True
    elif command.startswith('bpy.context'):
        split = command.split('=')
        if len(split) > 1:
            return split[0].split('.')[-1] + " = " + split[1]
        else:
            return ".".join(split[0].split('.')[-2:])
    else:
        return None
# endregion
