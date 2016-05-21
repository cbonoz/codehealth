import sublime, sublime_plugin
import json,random, traceback
from comment_parser import comment_parser
import os.path


import subprocess
import threading


COLOR_LIMIT = 100

#PARSER_SUPPORTED filetypes use python package comment engine 
PARSER_SUPPORTED = ["c","cpp","cc","java","js","go","sh"] #more here

#OUR_SUPPORTED filetypes use our comment engine 
OUR_SUPPORTED = ["py"]


import difflib
import sys, json, math
from redbaron import RedBaron

#scale used for calculating code decay amount
DEFAULT_DECAY_FACTOR = 50000

# DISTANCE_FACTOR = 5
# on_activated_count = 1
# on_load_count = 1
# ACTIVE = True

MAX_HEALTH = 100


def print_to_log(txt):
    with open("./log.txt","a+") as f:
            f.write(str(txt) + "\n")

def print_comments(comments):
    for c in comments:
        print_to_log(str(c))

def get_color(color):
    return "color_"+str(color)

def bash_command(cmd):
    return subprocess.check_output(cmd, shell=True)

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

def compare(s1, s2, decay_factor = DEFAULT_DECAY_FACTOR):
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
# global to share between activate and deactivate commands
colormap = {}


def clear_colors(self, view):
    global colormap

    print_to_log("clear_colors called with")
    print_to_log(str(colormap))
    # maparser_keys = colormap.keys()
    # for k in maparser_keys:
    #     view.erase_regions(get_color(k))
    for k in range(COLOR_LIMIT+1):
        view.erase_regions(get_color(k))

    colormap = {}

def parser_health_render(self, view, cs):
    print_to_log("parser_health_render\n")

    comment_regions = [sublime.Region(view.text_point(c._line_number-1, 0),view.text_point(c._line_number-1, len(c._text)+1)) for c in cs]

    #right now just assigns a random health score to each comment in the scope
    comment_regions = [(view.full_line(s),random.randint(0, COLOR_LIMIT)) for s in comment_regions]

    for c,color in comment_regions:
        color = str(color)
        if color in colormap:
            colormap[color].append(c)
        else:
            colormap[color] = [c]

        view.add_regions(get_color(color), colormap[color], get_color(color), "dot", 
            sublime.PERSISTENT)

def our_health_render(self, view, cs_list):
    print_to_log("our_health_render\n")
    cs = None
    try:
        cs = [item for sublist in cs_list for item in sublist]
    except Exception as e:
        cs = cs_list

    print_comments(cs)
    comment_regions = []
    comment_regions = [(sublime.Region(
        view.text_point(c.left_bounds[0]-1, c.left_bounds[1]-1),
        view.text_point(c.right_bounds[0]-1, c.right_bounds[1])),c._score) for c in cs]

    # length = len(comment_regions)
    for i, (c,color) in enumerate(comment_regions):

        color = str(color)
        if color in colormap:
            colormap[color].append(c)
        else:
            colormap[color] = [c]

        view.add_regions(get_color(color), colormap[color], get_color(color), "dot",
          sublime.PERSISTENT)


# class HighlightHealthCommand(sublime_plugin.EventListener):
#     # def on_post_save_async(self, view):
#     def on_modified_async(self, view):
#         # clear_colors(self,view)
#         sublime.status_message("on_modified")
#         cs = comment_parser.extract_comments(self.f_name)
#         parser_health_render(self, view, cs)

class ActivateHealthCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        activateHealthThread = ActivateHealthThread(self, edit)
        activateHealthThread.start()

class ActivateHealthThread(threading.Thread):
    def __init__(self, cmd, edit):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.view = cmd.view
        self.edit = edit

    def run(self):
        
        try:
            global colormap
            colormap = {}

            view = self.view
            self.f_name = view.file_name()
            self.file_ext = os.path.splitext(self.f_name)[1][1:].strip().lower()
            
            self.parser_supported = self.file_ext in PARSER_SUPPORTED
            self.our_supported = self.file_ext in OUR_SUPPORTED
            self.f_name = view.file_name()

            file_name = os.path.basename(self.f_name)
            print_to_log("Activate Health - " + file_name + " " + str(self.our_supported))

            if self.our_supported:
                #get the original file contents
                try:
                    git_root = bash_command("git rev-parse --show-toplevel")

                    rel_file_name = self.f_name[len(git_root):]
                    head_cmd = "git show HEAD:" + rel_file_name# + "> ~/.output_compare.py"
                    
                    print_to_log("cmd: " + head_cmd)

                    res = bash_command(head_cmd)
                    self.original_file_contents = str(res,'utf-8')

                    if (self.original_file_contents is None):
                        err = "Comment Health: Unable to get " + file_name + " from git"
                        sublime.status_message(err)
                        return
                        
                except Exception as e:
                    print_to_log("git error: " + str(e))
                    self.original_file_contents = None
                    self.supported = False

            elif not self.parser_supported:
                sublime.status_message("Comment Health - .%s not supported" % (self.file_ext))
                return

            clear_colors(self,view)

            # print_to_log("\n1---current text\n" + current_text)
            # print_to_log("\n2---head\n"+str(self.original_file_contents))

            print_progress(0)
            if self.parser_supported:
                cs = comment_parser.extract_comments(self.f_name)
                parser_health_render(self, view, cs)
            elif self.our_supported:
                current_text = view.substr(sublime.Region(0, view.size()))
                cs = compare(str(self.original_file_contents), str(current_text))
                our_health_render(self, view,cs)
            print_progress(100)

        
        except Exception as e:
            sublime.status_message("Error: " + str(e))
            print_to_log(traceback.format_exc())
            pass


class RemoveHealthCommand(sublime_plugin.TextCommand):
    def run(self, view):
        view = self.view
        sublime.status_message("Remove Health")
        clear_colors(self,view)
        return True

