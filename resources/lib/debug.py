# -*- coding: utf-8 -*-
import os, sys
if sys.version_info.major == 3:
    from .utils import setting, log
    from . import dialog
else:
    from utils import setting, log
    import dialog

class Debug(object):
    enabled = False
    traceback = None
    def __init__(self):
        self.set()

    def import_traceback(self):
        self.traceback = __import__('traceback')

    def exception_dialog(self, error):
        if debug.get() == False:
            log(error, xbmc.LOGERROR)
        dialog.error(error)

    def set(self):
        if setting('debug') == 'true':
            self.import_traceback()
            self.enabled = True
        else:
            self.enabled = False

    def get(self):
        return self.enabled

global debug
debug = Debug()
