# -*- coding: utf-8 -*-

from __future__ import print_function

import sublime
import sublime_plugin
import os
import threading
import subprocess
import functools
import re
from copy import copy
# https://pypi.python.org/pypi/comment_parser/1.0.3




IS_ST3 = sublime.version().startswith('3')


def get_settings():
    return sublime.load_settings("Codehealth.sublime-settings")

def get_vcs_settings():
    """
    Returns list of dictionaries
    each dict. represents settings for VCS
    """

    default = [
        {"name": "git", "dir": ".git", "cmd": "git"},
        {"name": "svn", "dir": ".svn", "cmd": "svn"},
        {"name": "bzr", "dir": ".bzr", "cmd": "bzr"},
        {"name": "hg",  "dir": ".hg",  "cmd": "hg"},
        {"name": "tf",  "dir": "$tf",  "cmd": "C:/Program Files (x86)/Microsoft Visual Studio 11.0/Common7/IDE/TF.exe"}
    ]
    settings = get_settings().get('vcs', default)

    # re-format settings array if user has old format of settings
    if type(settings[0]) == list:
        settings = [dict(name=name, cmd=cmd, dir='.'+name) for name, cmd in settings]

    return settings


def get_user_command(vcs_name):
    """
    Returns command that user specified for vcs_name
    """

    try:
        return [vcs['cmd'] for vcs in get_vcs_settings() if vcs.get('name') == vcs_name][0]
    except IndexError:
        return None



def get_vcs(directory):
    """
    Determines root directory for VCS and which of VCS systems should be used for a given directory

    Returns dictionary {name: .., root: .., cmd: .., dir: ..}
    """

    vcs_check = [(lambda vcs: lambda dir: os.path.exists(os.path.join(dir, vcs.get('dir', False)))
                 and vcs)(vcs) for vcs in get_vcs_settings()]

    start_directory = directory
    while directory:
        available = list(filter(bool, [check(directory) for check in vcs_check]))
        if available:
            available[0]['root'] = directory
            return available[0]

        parent = os.path.realpath(os.path.join(directory, os.path.pardir))
        if parent == directory:  # /.. == /
            # try TFS as a last resort
            # I'm not sure why we need to do this. Seems like it should find root for TFS in the main loop
            return tfs_root(start_directory)
        directory = parent

    return None


def main_thread(callback, *args, **kwargs):
    # sublime.set_timeout gets used to send things onto the main thread
    # most sublime.[something] calls need to be on the main thread
    sublime.set_timeout(functools.partial(callback, *args, **kwargs), 0)


def _make_text_safeish(text, fallback_encoding, method='decode'):
    # The unicode decode here is because sublime converts to unicode inside
    # insert in such a way that unknown characters will cause errors, which is
    # distinctly non-ideal... and there's no way to tell what's coming out of
    # git in output. So...
    try:
        unitext = getattr(text, method)('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        unitext = getattr(text, method)(fallback_encoding)
    except AttributeError:
        # strongly implies we're already unicode, but just in case let's cast
        # to string
        unitext = str(text)
    return unitext


def do_when(conditional, callback, *args, **kwargs):
    if conditional():
        return callback(*args, **kwargs)
    sublime.set_timeout(functools.partial(do_when, conditional, callback, *args, **kwargs), 50)


def log(*args, **kwargs):
    """
    @param *args: string arguments that should be logged to console
    @param debug=True: debug log mode
    @param settings=None: instance of sublime.Settings
    """
    debug = kwargs.get('debug', True)
    settings = kwargs.get('settings', None)

    if not settings:
        settings = get_settings()

    if debug and not settings.get('debug', False):
        return

    print('Codehealth:', *args)


class EditViewCommand(sublime_plugin.TextCommand):

    def run(self, edit, command=None, output='', begin=0, region=None):
        """
        For some reason Sublime's view.run_command() doesn't allow to pass tuples,
        therefore region must be a list
        """
        region = sublime.Region(int(region[0]), int(region[1])) if region else None
        if command == 'insert':
            self.view.insert(edit, int(begin), output)
        elif command == 'replace':
            self.view.replace(edit, region, output)
        elif command == 'erase':
            self.view.erase(edit, region)
        else:
            print('Invalid command: ', command)
            raise


class VcsCommand(object):
    may_change_files = False

    def __init__(self, *args, **kwargs):
        self.settings = get_settings()
        super(VcsCommand, self).__init__(*args, **kwargs)

    def log(self, *args, **kwargs):
        return log(settings=self.settings, *args, **kwargs)

    def run_command(self, command, callback=None, show_status=False,
                    filter_empty_args=True, **kwargs):
        if filter_empty_args:
            command = [arg for arg in command if arg]
        if 'working_dir' not in kwargs:
            kwargs['working_dir'] = self.get_working_dir()
        if 'fallback_encoding' not in kwargs and self.active_view() and self.active_view().settings().get('fallback_encoding'):
            kwargs['fallback_encoding'] = self.active_view().settings().get('fallback_encoding').rpartition('(')[2].rpartition(')')[0]
        kwargs['console_encoding'] = self.settings.get('console_encoding')

        autosave = self.settings.get('autosave', True)
        if self.active_view() and self.active_view().is_dirty() and autosave:
            self.active_view().run_command('save')
        if not callback:
            callback = self.generic_done

        log('run command:', ' '.join(command))
        thread = CommandThread(command, callback, **kwargs)
        thread.start()

        if show_status:
            message = kwargs.get('status_message', False) or ' '.join(command)
            sublime.status_message(message + 'wef')

    def generic_done(self, result):
        self.log('generic_done', result)
        if self.may_change_files and self.active_view() and self.active_view().file_name():
            if self.active_view().is_dirty():
                result = "WARNING: Current view is dirty.\n\n"
            else:
                # just asking the current file to be re-opened doesn't do anything
                print("reverting")
                position = self.active_view().viewport_position()
                self.active_view().run_command('revert')
                do_when(lambda: not self.active_view().is_loading(),
                        lambda: self.active_view().set_viewport_position(position, False))

        if not result.strip():
            return
        self.panel(result)

    def _output_to_view(self, output_file, output, clear=False,
                        syntax="Packages/Diff/Diff.tmLanguage"):
        output_file.set_syntax_file(syntax)
        if clear:
            output_file.run_command('edit_view', dict(command='replace', region=[0, self.output_view.size()], output=output))
        else:
            output_file.run_command('edit_view', dict(command='insert', output=output))

    def scratch(self, output, title=False, position=None, **kwargs):
        scratch_file = self.get_window().new_file()
        if title:
            scratch_file.set_name(title)
        scratch_file.set_scratch(True)
        self._output_to_view(scratch_file, output, **kwargs)
        scratch_file.set_read_only(True)
        if position:
            sublime.set_timeout(lambda: scratch_file.set_viewport_position(position), 0)
        return scratch_file

    def panel(self, output, **kwargs):
        if not hasattr(self, 'output_view'):
            self.output_view = self.get_window().get_output_panel("vcs")
        self.output_view.set_read_only(False)
        self._output_to_view(self.output_view, output, clear=True, **kwargs)
        self.output_view.set_read_only(True)
        self.get_window().run_command("show_panel", {"panel": "output.vcs"})

    def _active_file_name(self):
        view = self.active_view()
        if view and view.file_name() and len(view.file_name()) > 0:
            return view.file_name()

    def active_view(self):
        return self.view

    def get_window(self):
        if (hasattr(self, 'view') and hasattr(self.view, 'window')):
            return self.view.window()
        else:
            return sublime.active_window()

    def get_working_dir(self):
        return os.path.dirname(self._active_file_name())

    def is_enabled(self):
        file_name = self._active_file_name()
        if file_name and os.path.exists(file_name):
            return bool(get_vcs(self.get_working_dir()))
        return False



class ToggleHighlightChangesCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        setting_name = "highlight_changes"
        settings = get_settings()
        is_on = settings.get(setting_name)

        if is_on:
            # remove highlighting
            [self.view.erase_regions(k) for k in ('inserted', 'changed', 'deleted')]
        else:
            self.view.run_command('hl_changes')

        settings.set(setting_name, not is_on)
        sublime.save_settings("Codehealth.sublime-settings")


    
