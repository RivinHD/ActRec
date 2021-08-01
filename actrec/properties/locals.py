# region Imports
# blender modules
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, StringProperty, IntProperty

# relative Imports
from . import shared
from .. import functions, shared_data
# endregion

classes = []

class AR_local_actions(shared.AR_action, PropertyGroup):
    def update_temp_save(self, context):
        for i, x in enumerate(shared_data.local_temp):
            if x.id == self.id:
                shared_data.local_temp[i] = functions.property_to_python(self)
                return
    active : BoolProperty(default= True, update= update_temp_save, description= 'Toggles Macro on and off.')
classes.append(AR_local_actions)

class AR_local_load_text(PropertyGroup):
    name : StringProperty()
    apply : BoolProperty(default= False)
classes.append(AR_local_load_text)