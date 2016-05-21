import sublime, sublime_plugin
import json,math,random, traceback
from comment_parser import comment_parser
import os.path

import difflib
import sys, json
from redbaron import RedBaron

import subprocess


COLOR_LIMIT = 100
#PARSER uses provided comment engine (these are supported filetypes)
PARSER_SUPPORTED = ["c","cpp","cc","java","js","go","sh"] #more here
#CUSTOM uses our comment engine (these are supported filetypes)
CUSTOM_SUPPORTED = ["py"]


class Comment:
    def __init__(self, comment, score = 1):
        self._comment = comment
        self._score = int(score*100)
        
    def left_bounds(self):
        return (self._comment.absolute_bounding_box.top_left.line,
                self._comment.absolute_bounding_box.top_left.column)
    
    def right_bounds(self):
        return (self._comment.absolute_bounding_box.bottom_right.line,
                self._comment.absolute_bounding_box.bottom_right.column)
        
    def score(self):
        return self._score
        
    def __str__(self):
        return '<Comment left_bounds:{0} right_bounds:{1} score:{2}>'.format(
            self.left_bounds(),
            self.right_bounds(),
            self.score())

def print_comments(comments):
    for c in comments:
        print(c)

def ldiff(s1, s2, offset = 1):
    diff = difflib.ndiff(s1.splitlines(1), s2.splitlines(1))
    additions = set()
    
    current = offset
    
    total = 0        # Number of lines in the old file.
    changes = 0      # Number of changes, relative to the old file.
    changed = False
    
    for x in diff:
        if x.startswith('+ '):
            additions.add(current)
            current = current + 1
            changes = changes + 1
            changed = True
        elif x.startswith('- '):
            total = total + 1
            changes = changes + 1
            changed = True
        else:
            total = total + 1
            current = current + 1
    return (additions,
            float(changes) / total if total > 0 else 0)  

def compare(s1, s2):
    red1 = RedBaron(s1)
    red2 = RedBaron(s2)
    comments = []
    
    for f2 in red2.find_all('def'):
        f1 = red1.find('def', name = f2.name)        
        if f1 is not None:
            additions, cratio = ldiff(f1.dumps(), f2.dumps(),
                                f2.absolute_bounding_box.top_left.line)
            health = (1 - cratio) if cratio < 1 else 1
                                                       
            for c in f2.find_all('comment'):
                if cratio == 0 or \
                   c.absolute_bounding_box.top_left.line in additions:
                    comments.append(Comment(c))
                else:
                    comments.append(Comment(c, health))
        else:
            for c in f2.find_all('comment'):
                comments.append(Comment(c))
    
    return comments


"""
START PLUGIN CODE
"""

def get_color(color):
    return "color_"+str(color)

def bash_command(cmd):
    # proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, shell=True)
    # (out, err) = proc.communicate()
    out = subprocess.check_output(cmd, shell=True)
    print_to_log("program output:" + str(out))
    return out

def print_to_log(txt):
    with open("./log.txt","a+") as f:
            f.write(txt)

class HighlightHealthCommand(sublime_plugin.EventListener):

    def on_activated(self, view):
        try:
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
            try:
                self.original_file_contents = bash_command("git show HEAD:" + file_name)
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
        
        self.colormap = {}

    def p_health_render(self, view, cs):
        comment_regions = [sublime.Region(view.text_point(c._line_number-1, 0),view.text_point(c._line_number-1, len(c._text)+1)) for c in cs]
        comment_regions = [(view.full_line(s),random.randint(0, COLOR_LIMIT)) for s in comment_regions]



        comment_regions = [(view.full_line(s),random.randint(0, COLOR_LIMIT)) for s in comment_regions]
        # comment_regions = [(view.full_line(s),50) for s in comment_regions]

        for c,color in comment_regions:
            color = str(color)
            if color in self.colormap:
                self.colormap[color].append(c)
            else:
                self.colormap[color] = [c]

            view.add_regions(get_color(color), self.colormap[color], get_color(color), "dot",   sublime.DRAW_STIPPLED_UNDERLINE | sublime.PERSISTENT)
        sublime.status_message(str(comment_regions))



    def c_health_render(self, view, cs):
        for c in cs:
            print_to_log(str(c))

        comment_regions = [(sublime.Region(
            view.text_point(c.left_bounds[0], c.left_bounds[1]),
            view.text_point(c.right_bounds[0], c.right_bounds[1])),c._score) for c in cs]

  
        # comment_regions = [(view.full_line(s),50) for s in comment_regions]

        for c,color in comment_regions:
            color = str(color)
            if color in self.colormap:
                self.colormap[color].append(c)
            else:
                self.colormap[color] = [c]

            view.add_regions(get_color(color), self.colormap[color], get_color(color), "dot",   sublime.DRAW_STIPPLED_UNDERLINE | sublime.PERSISTENT)
        sublime.status_message(str(comment_regions))


    def on_post_save_async(self, view):
        # self.clear_colors(view) #merged 
        # def on_modified_async(self, view): # was this


        ### temporary block of health analysis execute ###
        if True:
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
                self.c_health_render(view,cs)
            
        except Exception as e:
            sublime.status_message("Error: " + str(e))
            print_to_log(traceback.format_exc())
            pass
            with open("./log.txt","a") as f:
                f.write(str(e))



class ActivateHealthCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        return True


class RemoveHealthCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        return True




