import sys, os, os.path
sys.path.append(os.path.dirname(__file__))
import difflib
import json, math, sys
from redbaron import RedBaron
import compare
import comment_parse
import random, traceback
import subprocess, time
import sublime, sublime_plugin

def flatten(l): return flatten(l[0]) + (flatten(l[1:]) if len(l) > 1 else []) if type(l) is list else [l]

#granularity for color scopes
COLOR_LIMIT = 100

#decay factor for other non-AST highlighted languages (non-python)
PARSER_DECAY_FACTOR = 20

# global to share between activate and deactivate commands
colormap = {}
#indicates if the plugin highlighting is active (toggled via sublime commands)
ACTIVE = True

PRINT_TO_LOG = False
LOG_FILE = "log.txt"
def print_to_log(txt):

    if PRINT_TO_LOG:
        with open(LOG_FILE,"a+") as f:
                f.write(str(txt) + "\n")

def print_comments(comments):
    for c in comments:
        print_to_log(str(c))

def get_color(color):
    return "color_"+str(color)

def bash_command(cmd, folder):
    return subprocess.check_output(cmd, cwd=folder,shell=True)


def print_progress(p):
    sublime.status_message("Running comment health...%s%%" % p)

"""
START PLUGIN CODE
"""

# naive implementation clears all region highlights (safe, but slow)
def clear_colors(self, view):
    for k in range(COLOR_LIMIT+1):
        view.erase_regions(get_color(k))
    global colormap
    colormap = {}

DIFFER = difflib.Differ()

#calculate comment decay from single change at a distance
def single_decay(distance):
    if distance != 0:
        return PARSER_DECAY_FACTOR/distance
    #division by zero due to deletion; deletion without addition does not affect decay
    return 0



# compute scoring function for current diff
def get_score_function(head_text, current_text):

    # diff = list(difflib.ndiff(head_text.splitlines(), current_text.splitlines()))
    try:
        diff = DIFFER.compare(head_text.splitlines(), current_text.splitlines())
        deltas = ('\n'.join(diff)).split("\n")
        # print_to_log("diff: %s, len %d" % (str(deltas), len(deltas)))
        print_to_log("diff len: %d" % (len(deltas)))



        line_num = 0
        line_deltas = set()
        exceptions = set()
        for line in deltas:
            # split off the diff type code
            code = line[:2]
            
            #if line addition or deletion mark as change
            if code == "+ ":
                line_num +=1
                # line_deltas.append(line_num)
                exceptions.add(line_num)
                line_deltas.add(line_num)
                # print_to_log("line %s: %s" % (str(line_num),str(line)))
            elif code == "- ":
                line_deltas.add(line_num)
            else:
                line_num += 1
            print_to_log("line %s: %s" % (str(line_num),str(line)))
                # line_deltas.append("%d: %s" % (lineNum, line[2:].strip()))

        exceptions = line_deltas

        print_to_log("line_deltas: %s\nexceptions: %s" % (str(line_deltas), str(exceptions)))

        

        #score comment (potentially multiline)
        def scoring_func(c):
            lines = c._text.count("\n")
            line_start = c._line_number
            line_end = line_start + lines
            line_numbers = set(range(line_start, line_end + 1))


            #if comment intersections an exception
            intersect = line_numbers.intersection(exceptions)
            if len(intersect)>0:
                print_to_log("comment %s healthy (line %s modified)" % (str(line_numbers),intersect))
                return compare.MAX_HEALTH

            decays = []

            def decay_function(x):
                return int(PARSER_DECAY_FACTOR/min(abs(x - line_start),abs(x - line_end)))

            change_lines = line_deltas.difference(intersect)
            decays = [decay_function(x) for x in change_lines]

            print_to_log("comment lines %s, decays: %s" % (str(line_numbers), str(decays)))
           
            return max(compare.MAX_HEALTH-sum(decays),0)

        return scoring_func
    except Exception as e:
        sublime.status_message("get_score_function, Error: " + str(e))
        print_to_log(traceback.format_exc())
        return None

#renders the list of comments/scores on the sublime view (using package parsing engine)
#right now just assigns a random health score to each comment in the scope
def parser_health_render(self, view, cs, score_function):
    comment_regions = [
        (view.full_line(sublime.Region(view.text_point(c._line_number-1, 0),view.text_point(c._line_number-1, len(c._text)+1))), score_function(c))
        for c in cs]
    #random.randint(0, COLOR_LIMIT)) 
    for c,color in comment_regions:
        color = str(color)
        print_to_log(str(c) + " " + color)
        if color in colormap:
            colormap[color].append(c)
        else:
            colormap[color] = [c]
        view.add_regions(get_color(color), colormap[color], get_color(color), "dot", 
            sublime.PERSISTENT)

#renders the list of comments/scores on the sublime view (using python parsing engine)
def python_health_render(self, view, cs):
    print_to_log("cs: " + str(cs))

    print_comments(cs)

    comment_regions = [
        (sublime.Region(view.text_point(c.left_bounds[0]-1, c.left_bounds[1]-1),view.text_point(c.right_bounds[0]-1, c.right_bounds[1])),c._score)
         for c in cs]

    for i, (c,color) in enumerate(comment_regions):
        color = str(color)
        if color in colormap:
            colormap[color].append(c)
        else:
            colormap[color] = [c]
        view.add_regions(get_color(color), colormap[color], get_color(color), "dot",
          sublime.PERSISTENT)


class HealthCommand(sublime_plugin.EventListener):
    # PARSER_SUPPORTED filetypes use python package comment engine 
    PARSER_SUPPORTED = ["c","cpp","cc","java","js","go","sh"]

    #python_SUPPORTED filetypes use python comment engine 
    python_SUPPORTED = ["py"]

    #static file content variables
    last_file = ""
    last_file_contents = None

    def setup(self, abs_file_name):
        # print_to_log("setup called")
        try:
            self.file_name = os.path.basename(abs_file_name)
            self.file_ext = os.path.splitext(abs_file_name)[1][1:].strip().lower()
            self.f_dir = os.path.dirname(abs_file_name)
            self.parser_supported = self.file_ext in HealthCommand.PARSER_SUPPORTED
            self.python_supported = self.file_ext in HealthCommand.python_SUPPORTED

            success = self.get_head_contents(abs_file_name)
            HealthCommand.last_file = abs_file_name

            print_to_log("setup successful")
        except Exception as e:
            sublime.status_message("setup, Error: " + str(e))
            print_to_log(traceback.format_exc())
            pass

        return success



    def get_head_contents(self, abs_file_name):
        supported = self.parser_supported or self.python_supported
        print_to_log("get_head_contents - " + self.file_name + " " + str(supported))

        if supported:
            git_root = bash_command("git rev-parse --show-toplevel",self.f_dir)
            rel_file_name = abs_file_name[len(git_root):]
            head_cmd = "git show HEAD:" + rel_file_name# + "> ~/.output_compare.py"
            print_to_log("cmd: " + head_cmd)
            res = bash_command(head_cmd,self.f_dir)

            HealthCommand.last_file_contents = str(res,'utf-8')

            if (HealthCommand.last_file_contents is None):
                err = "Comment Health: Unable to get " + self.file_name + " from git"
                sublime.status_message(err)
                return False

            return True
                    
        else:
            sublime.status_message("Comment Health - .%s not supported" % (self.file_ext))
            return False


    
    def render_health_scores(self, view):
        if not ACTIVE:
            # print_to_log("CodeHealth not active")
            return

        try:
            current_file = view.file_name()

            if (HealthCommand.last_file != current_file) or (not hasattr(self,"parser_supported")):
                print_to_log("loading contents: " + current_file)
                if not self.setup(current_file):
                    sublime.status_message("File " + current_file + " not supported by CH")

            current_text = view.substr(sublime.Region(0, view.size()))
            print_progress(0)
            if self.parser_supported:
                # comment_parser works off saved version! not local version (can't use on_modified)
                # my comment_parse does not have this restriction
                try:
                    print_to_log("parser '%s' current text len: %d" % (self.file_ext, len(current_text)))
                    cs = comment_parse.extract_comments(current_text, self.file_ext)
                    if len(cs) == 1:
                        print_to_log(str(cs[0]))
                    score_function = get_score_function(HealthCommand.last_file_contents, current_text)
                    print_to_log("parser comments _line_number (start lines): " + str([str(c._line_number) for c in cs]))
                    parser_health_render(self, view, cs, score_function)
                except Exception as e:
                    print_to_log(str(e))
                    return
            elif self.python_supported:
                print_to_log("Running python comment analysis")
                cs = compare.compare(HealthCommand.last_file_contents, current_text)
                # print_to_log("python_supported: " + str(compare.PYTHON_DECAY_FACTOR))
                python_health_render(self, view, cs)
            print_progress(100)

        except Exception as e:
            sublime.status_message("render_health, Error: " + str(e))
            print_to_log(str(traceback.format_exc()))
            pass

    #real-time updates on non-python (non-AST comment parsed) files
    #need to clear contents as insertion of new characters will shift current code health highlighted regions - can be improved
    def on_modified_async(self, view):
        # print_to_log("on_modified_async: " + self.parser_supported)
        if ".py" not in view.file_name():
            sublime.status_message("on_modified")
            clear_colors(self, view)
            self.render_health_scores(view)
        return


    #run for all parsers
    def on_post_save_async(self, view):
        # if ".py" not in view.file_name():
        print_to_log("on_post_save_async called")
        clear_colors(self,view)
        self.render_health_scores(view)
        
    def on_pre_close(self,view):
        clear_colors(self,view)

class ActivateHealthCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print_to_log("Activate Health")
        view = self.view
        global ACTIVE #use global keyword for assignment
        ACTIVE = True
        global PRINT_TO_LOG
        PRINT_TO_LOG = True
        sublime.status_message("Activate Health - Trigger on Save")

class RemoveHealthCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print_to_log("Remove Health")
        view = self.view
        clear_colors(self,view)
        global ACTIVE
        ACTIVE = False
        global PRINT_TO_LOG
        PRINT_TO_LOG = False
        sublime.status_message("Remove Health Trigger")





