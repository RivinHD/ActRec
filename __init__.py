from . import actrec

bl_info = actrec.config.info

def register():
    actrec.register()

def unregister():
    actrec.unregister()