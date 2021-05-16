# region Imports
# blender modules
import bpy

# relative imports
from . import update, config, preferences, log, operators
# endregion

# region Registration
def register():
    update.register()
    preferences.register()
    operators.register()
    for cls in ActionRecorder.classes:
        bpy.utils.register_class(cls)
    for cls in ActionRecorder.classespanel:
        bpy.utils.register_class(cls)
    for cls in ActionRecorder.blendclasses:
        try:
            bpy.utils.register_class(cls)
        except:
            continue
    ActionRecorder.Initialize_Props()
    log_sys.logger.info("Registered Action Recorder")

def unregister():
    for cls in ActionRecorder.classes:
        bpy.utils.unregister_class(cls)
    for cls in ActionRecorder.categoriesclasses:
        try:
            bpy.utils.unregister_class(cls)
        except:
            continue
    for cls in ActionRecorder.classespanel:
        bpy.utils.unregister_class(cls)
    for cls in ActionRecorder.blendclasses:
        try:
            bpy.utils.unregister_class(cls)
        except:
            continue
    ActionRecorder.Clear_Props()
    log.logger.info("Unregistered Action Recorder")
    log.log_sys.unregister()
# endregion