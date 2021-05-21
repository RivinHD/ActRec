# region Import
# external modules
import webbrowser
import uuid

# blender modules
import bpy
from bpy.types import Operator
from bpy.props import StringProperty
# endregion

classes = []

# region functions
def check_for_dublicates(l, name, num = 1): #Check for name duplicates and append .001, .002 etc.
    if name in l:
        return check_for_dublicates(l, name.split(".")[0] +".{0:03d}".format(num), num + 1)
    return name

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

# region Operators
class AR_OT_check_ctrl(Operator):
    bl_idname = "ar.check_ctrl"
    bl_label = "Check Ctrl"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        if event.ctrl:
            return {"FINISHED"}
        return {"CANCELLED"}
classes.append(AR_OT_check_ctrl)

class AR_OT_open_url(Operator):
    bl_idname = "ar.url_open"
    bl_label = "Open URL"

    url : StringProperty()
    description : StringProperty()

    def execute(self, context):
        webbrowser.open(self.url)
        return {"FINISHED"}

    @classmethod
    def description(context, properties):
        return properties.description
classes.append(AR_OT_open_url)
# endregion

# region PropertyGroups
class id_system: 
    def get_id(self):
        self['name'] = self.get('name', uuid.uuid4().hex)
        return self['name']

    name : StringProperty(get= get_id) # id and name are the same, because CollectionProperty use property 'name' as key
    id : StringProperty(get= get_id)   # both read-only
# endregion

# region Registration 
def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)
# endregion 
