import difflib
import sys
from redbaron import RedBaron

def ldiff(s1, s2, offset = 1):
    diff = difflib.ndiff(s1.splitlines(1), s2.splitlines(1))
    additions = set()
    changed = False
    current = offset
    for x in diff:
        if x.startswith('+ '):
            additions.add(current)
            changed = True
            current = current + 1
        elif x.startswith('- '):
            changed = True
        else:
            current = current + 1
    return additions, changed

def compare(s1, s2):
    red1 = RedBaron(s1)
    red2 = RedBaron(s2)
    fresh_comments = []
    stale_comments = []
    
    for f2 in red2.find_all('def'):
        f1 = red1.find('def', name = f2.name)        
        if f1 is not None:
            print f2.dumps()
            print f1.dumps()
            additions, changed = ldiff(f1.dumps(), f2.dumps(),
                                       f2.absolute_bounding_box.top_left.line)
            
            # We aren't concerned with functions that didn't change.
            if not changed:
                continue
                                           
            for c in f2.find_all('comment'):
                if c.absolute_bounding_box.top_left.line in additions:
                    fresh_comments.append(c)
                else:
                    stale_comments.append(c)
        else:
            for c in f2.find_all('comment'):
                fresh_comments.append(c)

    print [x.absolute_bounding_box for x in fresh_comments]
    print [x.absolute_bounding_box for x in stale_comments]
    return fresh_comments, stale_comments
    
if __name__ == '__main__':
    f1 = open(sys.argv[1], "r")
    f2 = open(sys.argv[2], "r")
    compare(f1.read(), f2.read())
              