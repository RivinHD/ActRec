# region Imports
# external modules
import os
import logging
import traceback

# blender modules
import bpy

# relative imports
from ..__init__ import bl_info
# endregion

# region Logsystem 
class log_system:
    def __init__(self, count: int) -> None:
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

        os.system.excepthook = self.exception_handler
    
    def exception_handler(self, exc_type, exc_value, exc_tb) -> None:
        traceback.print_exception(exc_type, exc_value, exc_tb)
        self.logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    def unregister(self) -> None:
        self.file_handler.close()
        self.logger.removeHandler(self.file_handler)
log_sys = log_system(5)
logger = log_sys.logger
#endregion 
