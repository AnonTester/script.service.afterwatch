# -*- coding: utf-8 -*-
import os, sys
import xbmc
import xbmcgui
if sys.version_info.major == 3:
    from . import utilxbmc
    from . import videolibrary
    from .utils import info, lang, setting, log
    from .debug import debug
else:
    import utilxbmc
    import videolibrary
    from utils import info, lang, setting, log
    from debug import debug

monitor = xbmc.Monitor()

class Progress:
    def __init__(self, steps):
        self.enable = setting('hide_progress') == 'false'
        self.steps = steps
        self.current = 0
        if steps > 0:
            if self.enable:
                if utilxbmc.version() >= 13:
                    self.bar = xbmcgui.DialogProgressBG()
                else:
                    self.bar = xbmcgui.DialogProgress()
                self.bar.create(info('name'))
                self.bar.update(0, info('name'))

    def start_module(self, module_title, module_steps):
        self.module_title = module_title
        self.module_steps = module_steps
        self.module_current = 0

    def update(self, msg):
        percent = int(self.current * 100 / self.steps)
        if self.enable:
            self.bar.update(percent, info('name'), lang(30531) % (self.module_title, msg))
        self.current += 1
        self.module_current += 1
        log('Progress.update: self.current=%s, self.module_current=%s' % (self.current, self.module_current))

    def finish_module(self):
        log('Progress.finish_module: self.module_steps=%s, self.module_current=%s' % (self.module_steps, self.module_current))
        if not self.module_steps == self.module_current:
            skip = self.module_steps - self.module_current
            self.current += skip
            self.module_current += skip
        percent = self.current * 100 / self.steps
        log('Progress.finish_module: self.current=%s, self.steps=%s' % (self.current, self.steps))
        if self.current == self.steps:
            if self.enable:
                log('Progress.finish_module: self.enable=%s' % (self.enable))
                self.bar.update(100, info('name'), 'Done')
                monitor.waitForAbort(1)
                self.bar.close()

    def update_library(self, path=False):
        if debug.get():
            log('remove_video setting set to %s' % (setting('remove_video')))
        if path and setting('remove_video') == 'true':
            if debug.get():
                log('removing video from video library %s' % (path))
            videolibrary.remove_video(path)

        if debug.get():
            log('update_library setting set to %s' % (setting('update_library')))
        if setting('update_library') == 'true':
            if debug.get():
                log('updating whole video library %s' % (path))
            xbmc.executebuiltin('UpdateLibrary(video)')
            while not xbmc.getCondVisibility('Library.IsScanningVideo'):
                pass
            while xbmc.getCondVisibility('Library.IsScanningVideo'):
                xbmc.sleep(20)
            percent = (self.current - 1) * 100 / self.steps
            if self.enable:
                self.bar.update(percent, info('name'),  lang(30531) % (self.module_title, lang(30513)))
            self.current += 1
            self.module_current += 1
            log('Progress.update_library: self.current=%s, self.module_current=%s' % (self.current, self.module_current))

