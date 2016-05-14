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
import base64
import requests



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


class CommandThread(threading.Thread):

    def __init__(self, command, on_done, working_dir="", fallback_encoding="", console_encoding="", **kwargs):
        threading.Thread.__init__(self)
        self.command = command
        self.on_done = on_done
        self.working_dir = working_dir
        if 'stdin' in kwargs:
            self.stdin = kwargs['stdin'].encode()
        else:
            self.stdin = None
        self.stdout = kwargs.get('stdout', subprocess.PIPE)
        self.console_encoding = console_encoding
        self.fallback_encoding = fallback_encoding
        self.kwargs = kwargs

    def run(self):
        try:
            # Per http://bugs.python.org/issue8557 shell=True is required to
            # get $PATH on Windows. Yay portable code.
            shell = os.name == 'nt'

            if self.working_dir != "":
                os.chdir(self.working_dir)

            if self.console_encoding:
                self.command = [s.encode(self.console_encoding) for s in self.command]

            proc = subprocess.Popen(self.command,
                                    stdout=self.stdout, stderr=subprocess.STDOUT,
                                    stdin=subprocess.PIPE,
                                    shell=shell, universal_newlines=False)
            output = proc.communicate(self.stdin)[0]
            if not output:
                output = ''
            # if sublime's python gets bumped to 2.7 we can just do:
            # output = subprocess.check_output(self.command)
            main_thread(self.on_done,
                        _make_text_safeish(output, self.fallback_encoding), **self.kwargs)
        except subprocess.CalledProcessError as e:
            main_thread(self.on_done, e.returncode)
        except OSError as e:
            if e.errno == 2:
                main_thread(sublime.error_message,
                            "'%s' binary could not be found in PATH\n\nConsider using `vcs` property to specify PATH\n\nPATH is: %s" % (self.command[0], os.environ['PATH']))
            else:
                raise e


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


class DiffCommand(VcsCommand):
    """ Here you can define diff commands for your VCS
        method name pattern: %(vcs_name)s_diff_command
    """

    def run(self, edit):
        vcs = get_vcs(self.get_working_dir())
        filepath = self.view.file_name()
        filename = os.path.basename(filepath)
        max_file_size = self.settings.get('max_file_size', 1024) * 1024
        if not os.path.exists(filepath) or os.path.getsize(filepath) > max_file_size:
            # skip large files
            return
        get_command = getattr(self, '{0}_diff_command'.format(vcs['name']), None)
        if get_command:
            self.run_command(get_command(filename), self.diff_done)

    def diff_done(self, result):
        self.log('diff_done', result)

    def git_diff_command(self, file_name):
        vcs_options = self.settings.get('vcs_options', {}).get('git') or ['--no-color', '--no-ext-diff']
        return [get_user_command('git') or 'git', 'diff'] + vcs_options + ['--', file_name]

    def svn_diff_command(self, file_name):
        params = [get_user_command('svn') or 'svn', 'diff']
        params.extend(self.settings.get('vcs_options', {}).get('svn', []))

        if '--internal-diff' not in params and self.settings.get('svn_use_internal_diff', True):
            params.append('--internal-diff')

        # if file starts with @, use `--revision HEAD` option
        # https://github.com/gornostal/Codehealth/issues/17
        if file_name.find('@') != -1:
            file_name += '@'
            params.extend(['--revision', 'HEAD'])

        params.append(file_name)
        return params

    def bzr_diff_command(self, file_name):
        vcs_options = self.settings.get('vcs_options', {}).get('bzr', [])
        return [get_user_command('bzr') or 'bzr', 'diff'] + vcs_options + [file_name]

    def hg_diff_command(self, file_name):
        vcs_options = self.settings.get('vcs_options', {}).get('hg', [])
        return [get_user_command('hg') or 'hg', 'diff'] + vcs_options + [file_name]

    def tf_diff_command(self, file_name):
        vcs_options = self.settings.get('vcs_options', {}).get('tf') or ['-format:unified']
        return [get_user_command('tf') or 'tf', 'diff'] + vcs_options + [file_name]

    def get_line_ending(self):
        return '\n'

    def join_lines(self, lines):
        """
        Join lines using os.linesep.join(), unless another method is specified in ST settings
        """
        return self.get_line_ending().join(lines)


class ShowDiffCommand(DiffCommand, sublime_plugin.TextCommand):
    def diff_done(self, result):
        self.log('on show_diff', result)

        if not result.strip():
            return

        result = result.replace('\r\n', '\n')
        file_name = re.findall(r'([^\\\/]+)$', self.view.file_name())
        self.scratch(result, title="Diff - " + file_name[0])


class DiffParser(object):
    instance = None

    def __init__(self, diff):
        self.diff = diff
        self.chunks = None
        self.__class__.instance = self

    def _append_to_chunks(self, start, lines):
        self.chunks.append({
            "start": start,
            "end": start + len(lines),
            "lines": lines
        })

    def get_chunks(self):
        if self.chunks is None:
            self.chunks = []
            diff = self.diff.strip()
            if diff:
                re_header = re.compile(r'^@@[0-9\-, ]+\+(\d+)', re.S)
                current = None
                lines = []
                for line in diff.splitlines():
                    # ignore lines with '\' at the beginning
                    if line.startswith('\\'):
                        continue

                    matches = re.findall(re_header, line)
                    if matches:
                        if current is not None:
                            self._append_to_chunks(current, lines)
                        current = int(matches[0])
                        lines = []
                    elif current:
                        lines.append(line)
                if current is not None and lines:
                    self._append_to_chunks(current, lines)

        return self.chunks

    def get_lines_to_hl(self):
        inserted = []
        changed = []
        deleted = []

        for chunk in self.get_chunks():
            current = chunk['start']
            deleted_line = None
            for line in chunk['lines']:
                if line.startswith('-'):
                    if (not deleted_line or deleted_line not in deleted):
                        deleted.append(current)
                    deleted_line = current
                elif line.startswith('+'):
                    if deleted_line:
                        deleted.pop()
                        deleted_line = None
                        changed.append(current)
                    elif current - 1 in changed:
                        changed.append(current)
                    else:
                        inserted.append(current)
                    current += 1
                else:
                    deleted_line = None
                    current += 1

        return inserted, changed, deleted

    def get_original_part(self, line_num):
        """ returns a chunk of code that relates to the given line
            and was there before Codehealthations

            return (lines list, start_line int, replace_lines int)
        """

        # for each chunk from diff:
        for chunk in self.get_chunks():
            # if line_num is within that chunk
            if chunk['start'] <= line_num <= chunk['end']:
                ret_lines = []
                current = chunk['start']  # line number that corresponds to current version of file
                first = None  # number of the first line to change
                replace_lines = 0  # number of lines to change
                return_this_lines = False  # flag shows whether we can return accumulated lines
                for line in chunk['lines']:
                    if line.startswith('-') or line.startswith('+'):
                        first = first or current
                        if current == line_num:
                            return_this_lines = True
                        if line.startswith('-'):
                            # if line starts with '-' we have previous version
                            ret_lines.append(line[1:])
                        else:
                            # if line starts with '+' we only increment numbers
                            replace_lines += 1
                            current += 1
                    elif return_this_lines:
                        break
                    else:
                        # gap between Codehealthations
                        # reset our variables
                        current += 1
                        first = current
                        replace_lines = 0
                        ret_lines = []
                if return_this_lines:
                    return ret_lines, first, replace_lines

        return None, None, None

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

BASE = "https://api.github.com" 

def github_getresult(url, params=None):
    r = requests.get(url, auth=(user, code),  params=params)
    return r.json()

def get_commits(repo):
    return github_getresult(BASE+"/repos/"+user+"/"+repo+"/commits")


def get_content(repo, path, params=None):
    url = BASE+"/repos/"+user+"/"+repo+"/contents/"+path
    if params is not None:
        url += "?" + "&".join([p[0]+"="+p[1] for p in params])
    return github_getresult(url)


def main():
    r = get_commits("cs230project")
    commits = [x["sha"] for x in r]
    print(commits)

    for c in commits[-5:-4]:
        r = get_content("cs230project", "README.md",[("ref", c)])
        content = r["content"]
        content = base64.b64decode(content)
        length = len(content)
        print(length, content)


if __name__ == "__main__":
    main()
    
