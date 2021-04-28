import bpy
from . import ActionRecorder as ActionRecorder
import logging
import os
import sys
import traceback

bl_info = {
    "name" : "ActionRecorder",
    "author" : "InamuraJIN, Rivin",
    "version": (3, 6, 5),
    "blender": (2, 83, 12),
    "location" : "View 3D",
    "warning" : "",
    "wiki_url" : "https://github.com/InamuraJIN/CommandRecorder/blob/master/README.md",# Documentation
    "tracker_url" : "https://twitter.com/Inamura_JIN",# Report Bug
    'link': 'https://twitter.com/Inamura_JIN',
    "category" : "System"
}

#Logging System
class Logger:
    def __init__(self, count: int):
        dirc = os.path.join(os.path.dirname(__file__), "logs")
        if not os.path.exists(dirc):
            os.mkdir(dirc)
        all_logs = os.listdir(dirc)
        loglater = []
        while len(all_logs) >= count:
            try:
                os.remove(min([os.path.join(dirc, filename) for filename in all_logs], key=os.path.getctime)) # delete oldest file
                all_logs = os.listdir(dirc)
            except PermissionError as err:
                loglater.append("File is already used -> PermissionError: " + str(err))
                break
        path = os.path.join(dirc, "ActRec_%s.log" % bpy.app.tempdir.split("\\")[-2].split("_")[1]) #get individuell id from blender tempdir

        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        file_formatter = logging.Formatter("%(levelname)s - %(relativeCreated)d - %(funcName)s - %(message)s")
        file_handler = logging.FileHandler(path, mode='w', encoding= 'utf-8', delay= True)
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        logger.info("Logging ActRec " + ".".join([str(x) for x in bl_info['version']]) + " running on Blender " + bpy.app.version_string)
        for log_text in loglater:
            logger.info(log_text)
        self.logger = logger
        self.file_handler = file_handler

        sys.excepthook = self.exception_handler
    
    def exception_handler(self, exc_type, exc_value, exc_tb):
        traceback.print_exception(exc_type, exc_value, exc_tb)
        self.logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    def unregister(self):
        self.file_handler.close()
        self.logger.removeHandler(self.file_handler)
log_sys = Logger(5)

def register():
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
    log_sys.logger.info("Unregistered Action Recorder")
    log_sys.unregister()
