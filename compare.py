import difflib
import sys
from redbaron import RedBaron

class Comment:
    def __init__(self, comment, score = 1):
        self.comment = comment
        self.score = score

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
    
    for c in comments:
        print c.comment
        print c.score
    return comments
    
if __name__ == '__main__':
    f1 = open(sys.argv[1], "r")
    f2 = open(sys.argv[2], "r")
    compare(f1.read(), f2.read())
              