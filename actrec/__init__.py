# region Imports
# blender modules
import bpy

# relative imports
from . import update, config, preferences, log, operators, ar_category, ar_global, ar_local
# endregion

# region Registration
def register():
    update.register()
    preferences.register()
    operators.register()
    ar_local.register()
    ar_category.register()
    ar_global.register()
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
    log.logger.info("Registered Action Recorder")

def unregister():
    update.unregister()
    preferences.unregister()
    operators.unregister()
    ar_local.unregister()
    ar_category.unregister()
    ar_global.unregister()
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