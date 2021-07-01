# region Imports
# external modules
import uuid
from collections import defaultdict

# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, IntProperty, CollectionProperty, BoolProperty

# relative imports
from ..log import logger
# endregion

classes = []

class data_manager:
    local_temp = defaultdict(list)
    global_temp = defaultdict(list)
    categories_temp = defaultdict(list)

# region PropertyGroups
class id_system: 
    def get_id(self):
        self['id'] = self.get('id', uuid.uuid1().hex)
        return self['id']

    def set_id(self, value: str):
        try:
            self['id'] = uuid.UUID(value).hex
        except ValueError as err:
            raise ValueError("%s with %s" %(err, value))

    name : StringProperty(get= get_id) # id and name are the same, because CollectionProperty use property 'name' as key
    id : StringProperty(get= get_id, set= set_id)   # create id by calling get-function of id

class AR_macro(id_system, PropertyGroup):
    label : StringProperty()
    macro : StringProperty()
    active : BoolProperty(default= True, update= SavePrefs, description= 'Toggles Macro on and off.')
    icon : IntProperty(default= 101) #Icon BLANK1 #Icon: MESH_PLANE (286) !!! change for local
    alert : BoolProperty(default= False)
    is_available : BoolProperty(default= True)
classes.append(AR_macro)

class AR_action(id_system, PropertyGroup):
    label : StringProperty()
    commands : CollectionProperty(type= AR_macro)
    icon : IntProperty(default= 101) #Icon BLANK1
    alert : BoolProperty(default= False)
classes.append(AR_action)
# endregion