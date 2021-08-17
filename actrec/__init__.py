# region Imports
# external modules
import json

# blender modules
import bpy
from bpy.app.handlers import persistent

# relative imports
from . import functions, menus, operators, panels, properties, ui_functions, uilist
from . import config, icon_manager, keymap, log, preferences, shared_data, update
# endregion

@persistent
def on_start(dummy = None):
    context = bpy.context
    AR = context.preferences.addons[__package__].preferences
    # load local actions
    if bpy.data.filepath == '':
        AR.local_actions.clear()
    if context.scene.ar.local == "{}" and context.scene.get('ar_local', None):   # load old local action data
        try:
            data = []
            old_data = json.loads(context.scene.get('ar_local'))
            for i, old_action in enumerate(old_data[0]['Commands'], 1):
                data.append({
                    "label": old_action['cname'],
                    "macros": [{
                        "label": old_macro['cname'],
                        "command": old_macro['macro'],
                        "active": old_macro['active'],
                        "icon": old_macro['icon']
                    } for old_macro in old_data[i]['Commands']],
                    "icon": old_action['icon']
                })
            context.scene.ar.local = json.dumps(data)
        except json.JSONDecodeError as err:
            log.logger.info("old scene-data couldn't be parsed (%s)" %err)
    functions.load_local_action(AR, json.dumps(context.scene.ar.local))
    # Check for update
    if AR.auto_update:
        bpy.ops.ar.update_check('EXEC_DEFAULT')
    # update paths
    AR.storage_path
    AR.icon_path
    functions.load(AR)
    functions.local_runtime_save(AR, None, False)
    functions.global_runtime_save(AR, False)
    functions.category_runtime_save(AR, False)

# region Registration
def register():
    menus.register()
    operators.register()
    panels.register()
    properties.register()
    uilist.register()
    icon_manager.register()
    update.register()
    keymap.register()
    preferences.register()

    handlers = bpy.app.handlers
    handlers.undo_post.append(functions.category_runtime_load)
    handlers.undo_post.append(functions.global_runtime_load)
    handlers.undo_post.append(functions.local_runtime_load)
    handlers.redo_post.append(functions.category_runtime_load)
    handlers.redo_post.append(functions.global_runtime_load)
    handlers.redo_post.append(functions.local_runtime_load)
    handlers.render_init.append(functions.execute_render_init)
    handlers.render_complete.append(functions.execute_render_complete)
    handlers.load_post.append(on_start)
    log.logger.info("Registered Action Recorder")

def unregister():
    menus.unregister()
    operators.unregister()
    panels.register()
    properties.unregister()
    uilist.register()
    icon_manager.unregister()
    update.unregister()
    keymap.unregister()
    preferences.unregister()
    
    handlers = bpy.app.handlers
    handlers.undo_post.remove(functions.category_runtime_load)
    handlers.undo_post.remove(functions.global_runtime_load)
    handlers.undo_post.remove(functions.local_runtime_load)
    handlers.redo_post.remove(functions.category_runtime_load)
    handlers.redo_post.remove(functions.global_runtime_load)
    handlers.redo_post.remove(functions.local_runtime_load)
    handlers.render_init.remove(functions.execute_render_init)
    handlers.render_complete.remove(functions.execute_render_complete)
    handlers.load_post.remove(on_start)
    log.logger.info("Unregistered Action Recorder")
    log.log_sys.unregister()
# endregion