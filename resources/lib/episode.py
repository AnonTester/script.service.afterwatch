# -*- coding: utf-8 -*-
import os, sys
import xbmc
if sys.version_info.major == 3:
    from . import utilxbmc
    from . import dialog
    from . import utilfile
    from .progress import Progress
    from .utils import log, info, lang, setting, set_setting, rpc, ValueErrorHandler
    from .video import Video
    from .debug import debug
    from urllib.parse import urlparse
else:
    import utilxbmc
    import dialog, utilfile, utilxbmc
    from progress import Progress
    from utils import log, info, lang, setting, set_setting, rpc, ValueErrorHandler
    from video import Video
    from debug import debug
    import urlparse

monitor = xbmc.Monitor()

class Episode(Video):
    def __init__(self):
        try:
            j = utilxbmc.xjson({
                "jsonrpc": "2.0",
                "method": "Player.GetItem",
                 "params": { "playerid": 1, "properties": ["file", "title", "showtitle", "playcount"] },
                 "id": 1
            })
            self.type = 'episode'
            self.episodeid = j['item']['id']
            self.path = j['item']['file']
            if setting('fm_alternate') == 'true' or [y for y in ("smb://", "nfs://") if self.path.lower().startswith(y)]:
                self.alt_method = True
            else:
                self.path = os.path.abspath(self.path)
                self.alt_method = False
            log("Episode: self.path=%s, self.alt_method=%s" % (self.path, self.alt_method))
            self.title = j['item']['title']
            self.showtitle = j['item']['showtitle']
            self.playcount = j['item']['playcount']
            self.rating = None
        except Exception as e:
            if debug.get():
                log(debug.traceback.print_exc(), xbmc.LOGERROR)
            debug.exception_dialog(e)

    MOVE_STEPS = 4
    def __move(self, progress):
        progress.start_module(lang(30131), self.MOVE_STEPS)
        try:
            progress.update(lang(30590)) # detecting library place
            lib_source = os.path.dirname(os.path.dirname(os.path.dirname(self.path)))
            if self.destination == lib_source:
                raise Exception(lang(30602))
            progress.update(lang(30506)) # moving files
            source = os.path.dirname(self.path)
            match = os.path.splitext(os.path.basename(self.path))[0]
            count = utilfile.count_manage_files(self.alt_method, source, match)
            if not dialog.warning(lang(30131), count):
                raise Exception(lang(30609))
            log("Episode.__move: source=%s" % source)
            if setting('fm_episodes_structure') == '0': # multiple folders
                destination = os.path.join(self.destination, self.path.split(os.sep)[-3], self.path.split(os.sep)[-2])
            else: # single folder
                destination = os.path.join(self.destination, self.path.split(os.sep)[-2])
            log("Episode.__move: destination=%s, self.alt_method=%s" % (destination, self.alt_method))
            utilfile.move_files(self.alt_method, source, destination, match, True)
            progress.update(lang(30513)) # updating library
            progress.update_library(self.path)
            self.path = os.path.join(destination, os.path.basename(self.path))
            self.episodeid = utilxbmc.get_episodeid_by_path(self.path)
            if self.episodeid: # if still in lib source folders
                progress.update(lang(30514)) # setting watched
                utilxbmc.set_episode_playcount(self.episodeid, self.playcount+1)
        except OSError:
            dialog.error(lang(30610))
        except ValueError as err:
            ValueErrorHandler(err)
        except Exception as e:
            if debug.get():
                log(debug.traceback.print_exc(), xbmc.LOGERROR)
            debug.exception_dialog(e)
        finally:
            progress.finish_module()


    DELETE_STEPS = 2
    def __delete(self, progress):
        progress.start_module(lang(30132), self.DELETE_STEPS)
        try:
            progress.update(lang(30516)) # deleting files
            source = os.path.dirname(self.path)
            remove_empty = setting('fm_episodes_remove_empty') == 'true'
            match = os.path.splitext(os.path.basename(self.path))[0]
            log("Episode.__delete: match=%s" % match)
            count = utilfile.count_manage_files(self.alt_method, source, match)
            if not dialog.warning(lang(30132), count):
                raise Exception(lang(30609))
            utilfile.delete_files(self.alt_method, source, match, remove_empty)
            progress.update(lang(30513)) # updating library
            progress.update_library(self.path)
            self.episodeid = None
            self.path = None
        except ValueError as err:
            ValueErrorHandler(err)
        except Exception as e:
            if debug.get():
                log(debug.traceback.print_exc(), xbmc.LOGERROR)
            debug.exception_dialog(e)
        finally:
            progress.finish_module()


    PRESERVE_PLAYCOUNT_STEPS = 1
    def __preserve_playcount(self, progress):
        progress.start_module(lang(30701), self.PRESERVE_PLAYCOUNT_STEPS)
        try:
            if not self.episodeid:
                raise Exception(lang(30601))
            progress.update(lang(30598)) # setting old playcount
            utilxbmc.set_episode_playcount(self.episodeid, self.playcount)
        except Exception as e:
            if debug.get():
                log(debug.traceback.print_exc(), xbmc.LOGERROR)
            debug.exception_dialog(e)
        finally:
            progress.finish_module()


    RATE_LIB_STEPS = 1
    def __rate_lib(self, progress):
        progress.start_module(lang(30204), self.RATE_LIB_STEPS)
        try:
            if not self.episodeid:
                raise Exception(lang(30601))
            progress.update(lang(30522)) # updating rating
            utilxbmc.set_episode_rating(self.episodeid, self.rating)
        except Exception as e:
            if debug.get():
                log(debug.traceback.print_exc(), xbmc.LOGERROR)
            debug.exception_dialog(e)
        finally:
            progress.finish_module()


    def ended(self):
        if setting('ps_episodes_quit_menu') == 'false' and setting('ps_episodes_logoff') == 'false' and setting('ps_episodes_display_off') == 'false' \
           and (not setting('fm_episodes_manage') or setting('fm_episodes_manage') == '0'): #episode management disabled and no post episode action set
        #if not setting('fm_episodes_manage') or setting('fm_episodes_manage') == '0': # episode management disabled
            log("Episode.ended: Not managing episodes, stop further processing")
            return
        restriction = setting('fm_episodes_restrictions')
        if restriction==1:
            excludelist = setting('fm_episodes_excludelist').lower().split(',')
            log("Episode.ended: excludelist=%s" % excludelist)
            if any(self.path.lower().find(v.strip()) >= 1 for v in excludelist):
                log("Episode.ended: Exclude word matched, stop further processing")
                return
        if restriction == '2':
            onlylist = setting('fm_episodes_onlylist').lower().split(',')
            log("Episode.ended: onlylist=%s" % onlylist)
            if not any(self.path.lower().find(v.strip()) >= 1 for v in onlylist):
                log("Episode.ended: Include word not matched, stop further processing")
                return
            else:
                log("Episode.ended: Include word matched, continue processing")

        excludefolder = setting('fm_episodes_excludefolder').lower()
        if not excludefolder == "":
            #remove username/password of smb source url
            if excludefolder.startswith('smb://'):
                parsed = urlparse(excludefolder)
                parseresult = parsed._replace(netloc="{}".format(parsed.hostname))
                excludefolder = parseresult.geturl()
            if self.path.lower().startswith(excludefolder):
                log("Episode.ended: Episode in excluded folder, stop further processing")
                return

        includefolder = setting('fm_episodes_includefolder').lower()
        if not includefolder == "":
            #remove username/password of smb source url
            if includefolder.startswith('smb://'):
                parsed = urlparse(includefolder)
                parseresult = parsed._replace(netloc="{}".format(parsed.hostname))
                includefolder = parseresult.geturl()
            if not self.path.lower().startswith(includefolder):
                log("Episode.ended: Episode not in included folder, stop further processing")
                return

        # pre confirm
        steps = 0
        move = False
        delete = False
        preserve_playcount = False
        rate_lib = False
        if setting('confirm') == 'true':
            wait_dialog = setting('wait_dialog')
            log("Episode.ended: confirm dialog %s sec delayed" % wait_dialog)
            if not (wait_dialog == '' or wait_dialog == '0'):
                monitor.waitForAbort(int(wait_dialog))
        if setting('fm_episodes_manage') == '2' or setting('fm_episodes_manage') == '3': # delete
            if dialog.proceed("%s - %s" % (self.showtitle, self.title), lang(30132)):
                delete = True
                steps += self.DELETE_STEPS
        if setting('fm_episodes_manage') == '1' or (setting('fm_episodes_manage') == '3' and not delete): # move
            if dialog.proceed("%s - %s" % (self.showtitle, self.title), lang(30131)):
                move = True
                steps += self.MOVE_STEPS
        if not setting('remove_video') == 'true':
            if setting('pt_episodes_playcount') == 'true':
                preserve_playcount = True
                steps += self.PRESERVE_PLAYCOUNT_STEPS
            if setting('rt_episodes_lib') == 'true':
                rate_lib = True
                steps += self.RATE_LIB_STEPS
        # pre settings
        if move:
            destination = setting('fm_episodes_destination')
            if self.alt_method or destination.lower().startswith('smb://') or destination.lower().startswith('nfs://'):
                self.alt_method = True
            else:
                self.destination = os.path.abspath(destination)
            while not self.destination or self.destination == '.':
                destination = xbmcgui.Dialog.browse(3, lang(30525) % info('name'), 'files')
                if self.alt_method or destination.lower().startswith('smb://') or destination.lower().startswith('nfs://'):
                    self.alt_method = True
                else:
                    self.destination = os.path.abspath(destination)
            log("Episode.ended: fm_episodes_destination=%s, alt_method=%s" % (self.destination, self.alt_method))
            set_setting('fm_episodes_destination', self.destination)
        # pre context
        # pre process
        progress = Progress(steps)
        if not setting('remove_video') == 'true':
            if rate_lib:
                rating = dialog.rating(self.title)
                while not rating:
                    rating = dialog.rating(self.title)
                self.rating = rating
            if preserve_playcount:
                self.__preserve_playcount(progress)
            if rate_lib:
                self.__rate_lib(progress)
        if move:
            self.__move(progress)
        elif delete:
            self.__delete(progress)

        # post confirm
        quit_menu = False
        logoff = False
        display_off = False
        if setting('ps_episodes_quit_menu') == 'true':
            if dialog.proceed("%s - %s" % (self.showtitle, self.title), lang(30402)):
                quit_menu = True
        if setting('ps_episodes_logoff') == 'true':
            if dialog.proceed("%s - %s" % (self.showtitle, self.title), lang(30407)):
                logoff = True
        if setting('ps_episodes_display_off') == 'true':
            if dialog.proceed("%s - %s" % (self.showtitle, self.title), lang(30404)):
                display_off = True
        # post processing
        if quit_menu:
            self.show_quit_menu()
        if logoff:
            self.logoff_user()
        if display_off:
            self.turn_display_off()
