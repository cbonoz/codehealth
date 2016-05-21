import sublime, sublime_plugin
import json,random, traceback
from comment_parser import comment_parser
import os.path


import subprocess


COLOR_LIMIT = 100
#PARSER uses provided comment engine (these are supported filetypes)
PARSER_SUPPORTED = ["c","cpp","cc","java","js","go","sh"] #more here
#CUSTOM uses our comment engine (these are supported filetypes)
CUSTOM_SUPPORTED = ["py"]

#is the plugin active (if it is, run the code health analysis on save)
ACTIVE = True


def get_color(color):
    return "color_"+str(color)

def bash_command(cmd):
    # proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=True)
    # (out, err) = proc.communicate()
    out = subprocess.check_output(cmd, shell=True)
    # print_to_log("program output:" + str(out))
    return out


import difflib
import sys, json, math
from redbaron import RedBaron

#scale used for calculating code decay amount
DEFAULT_DECAY_FACTOR = 5000

# DISTANCE_FACTOR = 5

on_activated_count = 1
on_load_count = 1

MAX_HEALTH = 100


def print_to_log(txt):
    with open("./log.txt","a+") as f:
            f.write(str(txt) + "\n")


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

def print_comments(comments):
    for c in comments:
        print(c)
        print_to_log(c)


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
    red1 = RedBaron(s1)
    red2 = RedBaron(s2)
    result = []
    
    for ast_f2 in red2.find_all('def'):
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
    
    return result



if __name__ == '__main__':
    f1 = open(sys.argv[1], "r")
    f2 = open(sys.argv[2], "r")
    print_comments(compare(f1.read(), f2.read()))

"""
START PLUGIN CODE
"""


class HighlightHealthCommand(sublime_plugin.EventListener):

    def on_load_async(self, view):
        global on_load_count
        print_to_log("on_load: " + str(on_load_count))
        on_load_count+=1

    def on_activated_async(self, view):
        try:
            global on_activated_count
            print_to_log("on_activated: " + str(on_activated_count))
            on_activated_count+=1


            self.f_name = view.file_name()
            self.file_ext = os.path.splitext(self.f_name)[1][1:].strip().lower()
            self.colormap = {}
            self.p_supported = self.file_ext in PARSER_SUPPORTED
            self.c_supported = self.file_ext in CUSTOM_SUPPORTED
            self.supported = self.p_supported or self.c_supported

            self.f_name = view.file_name()

            # with open(self.f_name,"r") as f:
            #         self.original_file_contents = f.read() #to be used for diff 
            file_name = os.path.basename(self.f_name)

            if ("codehealth" in file_name):
                ACTIVE = False

            if self.c_supported:
                try:
                    if ("output_compare" not in file_name):
                        self.original_file_contents = bash_command("git show HEAD:" + file_name + "> output_compare.py")
                except Exception as e:
                    self.original_file_contents = None
                    self.supported = False

            supported_text = "supported" if (self.supported) else "not supported"
            sublime.status_message("Comment Health - %s %s" % (self.file_ext, supported_text))

        except Exception as e:
            sublime.status_message(str(e))
            pass

    def clear_colors(self, view):
        map_keys = self.colormap.keys()

        for k in map_keys:
            view.erase_regions(get_color(k))
        test = 1
        self.colormap = {}

    def p_health_render(self, view, cs):
        comment_regions = [sublime.Region(view.text_point(c._line_number-1, 0),view.text_point(c._line_number-1, len(c._text)+1)) for c in cs]
        comment_regions = [(view.full_line(s),random.randint(0, COLOR_LIMIT)) for s in comment_regions]

        for c,color in comment_regions:
            color = str(color)
            if color in self.colormap:
                self.colormap[color].append(c)
            else:
                self.colormap[color] = [c]

            view.add_regions(get_color(color), self.colormap[color], get_color(color), "dot",   sublime.DRAW_STIPPLED_UNDERLINE | sublime.PERSISTENT)
        sublime.status_message(str(comment_regions))



    def c_health_render(self, view, cs):
        comment_regions = [(sublime.Region(
            view.text_point(c.left_bounds[0]-1, c.left_bounds[1]),
            view.text_point(c.right_bounds[0]-1, c.right_bounds[1])),c._score) for c in cs]


        # comment_regions = [(view.full_line(s),50) for s in comment_regions]

        for c,color in comment_regions:
            color = str(color)
            if color in self.colormap:
                self.colormap[color].append(c)
            else:
                self.colormap[color] = [c]

            view.add_regions(get_color(color), self.colormap[color], get_color(color), "dot",   sublime.DRAW_STIPPLED_UNDERLINE | sublime.PERSISTENT)
        sublime.status_message(str(comment_regions))

    # def on_modified_async(self, view): # was this
    def on_post_save_async(self, view):
 
        ### temporary block of health analysis execute ###
        if True:#(not self.c_supported) or (not ACTIVE):#True:
            return

        try:
            self.clear_colors(view)
            cs = None

            if self.p_supported:
                cs = comment_parser.extract_comments(self.f_name)
                self.p_health_render(view, cs)
            elif self.c_supported:
                current_text = view.substr(sublime.Region(0, view.size()))
                cs = compare(str(self.original_file_contents), str(current_text))
                print_comments(cs)
                self.c_health_render(view,cs)
            
        except Exception as e:
            sublime.status_message("Error: " + str(e))
            print_to_log(traceback.format_exc())
            pass
