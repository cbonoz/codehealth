import difflib
import json, math, sys
from redbaron import RedBaron

"""
Compare.py
"""

#max health value
MAX_HEALTH = 100

#scale used for calculating code decay amount
OUR_DECAY_FACTOR = 10

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
        return result

    except Exception as e:
        err = "CommentHealth compare error: " + str(e)
        # sublime.status_message(err)
        return []
        

