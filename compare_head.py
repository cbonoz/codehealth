import difflib
import math
import sys
from redbaron import RedBaron

DISTANCE_FACTOR = 1
MAX_HEALTH = 100

class Comment:
    def __init__(self, comment, score = MAX_HEALTH):
        self._comment = comment
        self._score = score
        
    def left_bounds(self):
        return (self._comment.absolute_bounding_box.top_left.line,
                self._comment.absolute_bounding_box.top_left.column)
    
    def right_bounds(self):
        return (self._comment.absolute_bounding_box.bottom_right.line,
                self._comment.absolute_bounding_box.bottom_right.column)
        
    def score(self):
        return self._score
        
    def setScore(self, score):
        self._score = score
        
    def __str__(self):
        return '<Comment left_bounds:{0} right_bounds:{1} score:{2}>'.format(
            self.left_bounds(),
            self.right_bounds(),
            self.score())

def print_comments(comments):
    for c in comments:
        print(c)

def preprocess_files(s1, s2, offset = 1.0):
    diff = difflib.ndiff(s1.splitlines(1), s2.splitlines(1))
    additions = []
    deletions = [] # Deletion position assuming all the additions already occurred.
    current = offset
    test = 1
    test = 5

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
    for ast_c in f.find_all('comment'):
        comment = Comment(ast_c)
        line, _ = comment.left_bounds()
        if line not in excludes:
            comments.append(comment)
        
    return comments

def compare(s1, s2):
    red1 = RedBaron(s1)
    red2 = RedBaron(s2)
    result = []
    
    for ast_f2 in red2.find_all('def'):
        ast_f1 = red1.find('def', name = ast_f2.name)        
        if ast_f1 is not None:
            additions, deletions = preprocess_files(ast_f1.dumps(),
                                                    ast_f2.dumps())
            comments = preprocess_comments(ast_f2, additions) 
            for a in additions:
                for c in comments:
                    line, _ = c.left_bounds()
                    distance = math.fabs(line - a)
                    score = int(c.score() - float(DISTANCE_FACTOR) / (distance * distance))
                    c.setScore(score if score > 0 else 0)
            for d in deletions:
                for c in comments:
                    line, _ = c.left_bounds()
                    line = line + 1 if line >= d else line
                    distance = math.fabs(line - d)
                    score = int(c.score() - float(DISTANCE_FACTOR) / (distance * distance))
                    c.setScore(score if score > 0 else 0)
            result.extend(comments)
        else:
            result.extend(preprocess_comments(ast_f2, []))
    
    return result

if __name__ == '__main__':
    f1 = open(sys.argv[1], "r")
    f2 = open(sys.argv[2], "r")
    print_comments(compare(f1.read(), f2.read()))
              