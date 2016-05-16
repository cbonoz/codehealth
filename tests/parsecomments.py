from comment_parser import comment_parser
cs = comment_parser.extract_comments("freq.c")
print(len(cs))
for comment in cs:
    print(comment.__dict__)