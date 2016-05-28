import sys,os, os.path
sys.path.append(os.path.dirname(__file__))

import difflib
import json, math
from redbaron import RedBaron
import sublime, sublime_plugin
import random, traceback
from comment_parser import comment_parser

import subprocess, time
# import threading

#granularity for color scopes
COLOR_LIMIT = 100

#scale used for calculating code decay amount
OUR_DECAY_FACTOR = 8000

#max health value
MAX_HEALTH = 100

# global to share between activate and deactivate commands
colormap = {}

#indicates if the plugin highlighting is active (toggled via sublime commands)
ACTIVE = True

def print_to_log(txt):
    with open("./log.txt","a+") as f:
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
Compare.py
"""

class Comment:
    def __init__(self, comment, score = MAX_HEALTH):
        self._comment = comment
        self._score = score
        self.left_bounds = (self._comment.absolute_bounding_box.top_left.line,
                self._comment.absolute_bounding_box.top_left.column)
        self.right_bounds = (self._comment.absolute_bounding_box.bottom_right.line,
                self._comment.absolute_bounding_box.bottom_right.column)
        
    def score(self):
        return self._score
        
    def setScore(self, score):
        self._score = score
        
    def __str__(self):
        return '<Comment left_bounds:{0} right_bounds:{1} score:{2}>'.format(
            self.left_bounds,
            self.right_bounds,
            self.score())

def preprocess_files(s1, s2, offset = 1.0):
    diff = difflib.ndiff(s1.splitlines(1), s2.splitlines(1))
    additions = []
    deletions = [] # Deletion position assuming aldfsl the additions already occurred. 
    current = offset

    for x in diff:
        if x.startswith('+ '):
            additions.append(current)
            current = current + 1
        elif x.startswith('- '):
            deletions.append(current)
        else:
            current = current + 1
    
    return additions, deletions

def preprocess_comments(f, excludes):
    comments = []
    exceptions = []
    for ast_c in f.find_all('comment'):
        comment = Comment(ast_c)
        line, _ = comment.left_bounds
        if line not in excludes:
            comments.append(comment)
        else:
            exceptions.append(comment)
        
    return comments, exceptions

def compare(s1, s2, decay_factor = OUR_DECAY_FACTOR):
    # print_to_log("called compare")
    try:
        red1 = RedBaron(s1)
        red2 = RedBaron(s2)
        result = []

        defs = red2.find_all('def')
        length = len(defs)
        for ast_f2 in defs:
            ast_f1 = red1.find('def', name = ast_f2.name)        
            if ast_f1 is not None:
                additions, deletions = preprocess_files(ast_f1.dumps(),
                                                        ast_f2.dumps())
                comments, exceptions = preprocess_comments(ast_f2, additions) 
                for a in additions:
                    for c in comments:
                        line, _ = c.left_bounds
                        distance = math.fabs(line - a)
                        score = int(c.score() - float(decay_factor) / (distance * distance))
                        c.setScore(score if score > 0 else 0)
                for d in deletions:
                    for c in comments:
                        line, _ = c.left_bounds
                        line = line + 1 if line >= d else line
                        distance = math.fabs(line - d)
                        score = int(c.score() - float(decay_factor) / (distance * distance))

                        c.setScore(score if score > 0 else 0)
                result.extend(comments)
                result.extend(exceptions)
            else:
                result.extend(preprocess_comments(ast_f2, []))

        result = [r for r in result if r != []]
        print_to_log("compare result: " + str(result))
        return result

    except Exception as e:
        err = "CommentHealth compare error: " + str(e)
        print_to_log(err)
        sublime.status_message(err)
        return []
        

if __name__ == '__main__':
    f1 = open(sys.argv[1], "r")
    f2 = open(sys.argv[2], "r")
    print_comments(compare(f1.read(), f2.read()))


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

# compute scoring function for current diff
def get_score_function(head_text, current_text):

    # diff = list(difflib.ndiff(head_text.splitlines(), current_text.splitlines()))
    try:
        diff = DIFFER.compare(current_text.splitlines(), head_text.splitlines())
        # deltas = '\n'.join(diff)
        lineNum = 0
        line_deltas = list()
        for line in diff:
            # split off the code
            code = line[:2]
            # if the  line is in both files or just b, increment the line number.
            # if code in ("  ", "+ "):
            lineNum += 1
            # if this line is only in b, print the line number and the text on the line
            if code == "+ " or code == "- ":
                line_deltas.append(lineNum)
                # line_deltas.append("%d: %s" % (lineNum, line[2:].strip()))

        def f(line_number):
            # return 0
            decay_factor = 20
            decays = list(map(lambda x: int(decay_factor/(abs(x - line_number))), [x for x in line_deltas if x != line_number]))
            # print_to_log("comment line %s, decays: %s" % (line_number, str(decays)))
           
            return max(MAX_HEALTH-sum(decays),0)

        return f
    except Exception as e:
        sublime.status_message("Error: " + str(e))
        print_to_log(traceback.format_exc())
        return None

#renders the list of comments/scores on the sublime view (using package parsing engine)
#right now just assigns a random health score to each comment in the scope
def parser_health_render(self, view, cs, score_function):
    comment_regions = [
        (view.full_line(sublime.Region(view.text_point(c._line_number-1, 0),view.text_point(c._line_number-1, len(c._text)+1))), score_function(c._line_number))
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

#renders the list of comments/scores on the sublime view (using our parsing engine)
def our_health_render(self, view, cs_list):
    cs = None
    #flatten the list if needed
    try:
        cs = [item for sublist in cs_list for item in sublist]
    except Exception as e:
        cs = cs_list

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

    #OUR_SUPPORTED filetypes use our comment engine 
    OUR_SUPPORTED = ["py"]
    # TIME_DIFF = 5000 #ms for running again

    #static content variables
    last_file = ""
    last_file_contents = None
    last_execute = 0

    def setup(self, abs_file_name):
        # print_to_log("setup called")
        try:
            self.file_name = os.path.basename(abs_file_name)
            self.file_ext = os.path.splitext(abs_file_name)[1][1:].strip().lower()
            self.f_dir = os.path.dirname(abs_file_name)
            self.parser_supported = self.file_ext in HealthCommand.PARSER_SUPPORTED
            self.our_supported = self.file_ext in HealthCommand.OUR_SUPPORTED

            self.get_head_contents(abs_file_name)
            HealthCommand.last_file = abs_file_name

            print_to_log("setup successful")
        except Exception as e:
            sublime.status_message("Error: " + str(e))
            print_to_log(traceback.format_exc())
            pass


    def get_head_contents(self, abs_file_name):
        supported = self.parser_supported or self.our_supported
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
                    
        else:
            sublime.status_message("Comment Health - .%s not supported" % (self.file_ext))


    
    def render_health_scores(self, view):
        global ACTIVE
        if not ACTIVE:
            print_to_log("health not active")
            return

        try:
            current_file = view.file_name()

            if (HealthCommand.last_file != current_file):
                print_to_log("loading contents: " + current_file)
                self.setup(current_file)

            current_text = view.substr(sublime.Region(0, view.size()))
            print_progress(0)
            if self.parser_supported:
                # comment_parser works off saved version! not local version (can't use on_modified)
                cs = comment_parser.extract_comments(current_file) 
                score_function = get_score_function(HealthCommand.last_file_contents, current_text)
                parser_health_render(self, view, cs, score_function)
            elif self.our_supported:
                cs = compare(HealthCommand.last_file_contents, current_text)
                our_health_render(self, view, cs)
            print_progress(100)

        except Exception as e:
            sublime.status_message("Error: " + str(e))
            print_to_log(traceback.format_exc())
            pass

    def on_modified_async(self, view):
        #need to clear contents as insertion of new characters will shift current code health highlighted regions - unless a more clever way to do this
        # clear_colors(self, view)
        # self.render_health_scores(view)
        return

    def on_post_save_async(self, view):
        print_to_log("HealthCommand: on_post_save_async called")
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
        sublime.status_message("Activate Health - Trigger on Save")

class RemoveHealthCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        print_to_log("Remove Health")
        view = self.view
        clear_colors(self,view)
        global ACTIVE
        ACTIVE = False
        sublime.status_message("Remove Health Trigger")
