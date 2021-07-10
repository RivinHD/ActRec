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
        active_action = AR.local_actions[AR.selected_local_action_index]
        action = shared_data.data_manager.local_temp.get(active_action.id)
        if action is None:
            return
        action[self.id] = functions.property_to_python(self)

    label : StringProperty()
    macro : StringProperty()
    active : BoolProperty(default= True, update= update_temp_save, description= 'Toggles Macro on and off.')
    icon : IntProperty(default= 101) #Icon BLANK1 #Icon: MESH_PLANE (286) !!! change for local
    alert : BoolProperty(default= False)
    is_available : BoolProperty(default= True)
classes.append(AR_macro)

class AR_action(id_system, PropertyGroup):
    def get_value(self) -> bool:
        return self.get("selected", False)
    def set_value(self, value: bool) -> None:
        AR = bpy.context.preferences.addons[__package__].preferences
        parent_name = self.path_from_id().split('[')[0]
        selection_list_name = "%s.selected_ids" %parent_name
        selected_ids = AR.get(selection_list_name, [])
        if value:
            ctrl_value = bpy.ops.ar.check_ctrl('INVOKE_DEFAULT')
            if selected_ids != [] and ctrl_value == 'CANCELLED':
                AR[selection_list_name].clear()
                for selected_id in selected_ids:
                    AR.global_actions[selected_id].selected = False
            AR.set_default(selection_list_name, [])
            AR[selection_list_name].append(self.id)
            self['selected'] = value
        elif not (self.id in selected_ids):
            self['selected'] = value
            
    label : StringProperty()
    commands : CollectionProperty(type= AR_macro)
    icon : IntProperty(default= 101) #Icon BLANK1
    alert : BoolProperty(default= False)
    selected : BoolProperty(default= False, set= set_value, get= get_value, description= "Select this Action Button\n use ctrl to select muliple", name = 'Select')
classes.append(AR_action)
# endregion