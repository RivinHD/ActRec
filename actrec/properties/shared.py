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
from .. import functions, shared_data
# endregion

classes = []

# region PropertyGroups
class id_system: 
    def get_id(self):
        self['name'] = self.get('name', uuid.uuid1().hex)
        return self['name']
    def set_id(self, value: str):
        try:
            self['name'] = uuid.UUID(value).hex
        except ValueError as err:
            raise ValueError("%s with %s" %(err, value))

    name : StringProperty(get= get_id) # id and name are the same, because CollectionProperty use property 'name' as key
    id : StringProperty(get= get_id, set= set_id)   # create id by calling get-function of id

class AR_macro(id_system, PropertyGroup):
    def update_temp_save(self, context):
        AR = bpy.context.preferences.addons[__package__].preferences
        for i, x in enumerate(shared_data.local_temp):
            if x.id == self.id:
                shared_data.local_temp[i] = functions.property_to_python(self)
                return

    label : StringProperty()
    macro : StringProperty()
    active : BoolProperty(default= True, update= update_temp_save, description= 'Toggles Macro on and off.')
    icon : IntProperty(default= 101) #Icon BLANK1 #Icon: MESH_PLANE (286) !!! change for local
    alert : BoolProperty(default= False)
    is_available : BoolProperty(default= True)
classes.append(AR_macro)

class AR_action(id_system):
    label : StringProperty()
    commands : CollectionProperty(type= AR_macro)
    icon : IntProperty(default= 101) #Icon BLANK1 #Icon: MESH_PLANE (286) !!! change for local
    alert : BoolProperty(default= False)

class AR_scene_data(PropertyGroup): # as Scene PointerProperty
    local : StringProperty(name= "Local", description= 'Scene Backup-Data of AddonPreference.local_actions (json format)', default= '{}')
classes.append(AR_scene_data)
# endregion