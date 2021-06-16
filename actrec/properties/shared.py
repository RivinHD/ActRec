# region Imports
# external modules
import uuid

# blender modules
import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty

# relative imports
from ..log import logger
# endregion

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
    id : StringProperty(get= get_id, set= set_id)   # name is read-only
# endregion