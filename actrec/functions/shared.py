
# region functions
def check_for_dublicates(l, name, num = 1): #Check for name duplicates and append .001, .002 etc.
    if name in l:
        return check_for_dublicates(l, name.split(".")[0] +".{0:03d}".format(num), num + 1)
    return name

def property_to_python(property):
    if hasattr(property, 'id_data'):
        id_property = property.id_data
        if property == id_property:
            return property
        if property.__class__.__name__ == 'bpy_prop_collection_idprop':
            data = []
            for item in property:
                data_dict = {}
                for attr in item.bl_rna.property[1:]:
                    identifier = attr.identifier
                    data_dict[identifier] = property_to_python(getattr(item, identifier))
                data.append(data_dict)
            return data
        else:
            data = {}
            for attr in property.bl_rna.property[1:]:
                identifier = attr.identifier
                data[identifier] = property_to_python(getattr(property, identifier))
            return data
    return property
    

def add_data_to_collection(collection, data) -> None:
    new_item = collection.add()
    for key, value in data.items():
        if isinstance(value, list):
            for element in value:
                add_data_to_collection(new_item[key], element)
        elif isinstance(value, dict):
            add_data_to_collection(new_item[key], value)
        else:
            new_item[key] = value
                
def insert_to_collection(collection, index, data) -> None:
    add_data_to_collection(collection, data)
    collection.move(len(collection) - 1, index)
# endregion
