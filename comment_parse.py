#!/usr/bin/python
"""
This program parses various source files and extracts the comment texts.

Currently supported languages:
    C
    C++
    Go
    Java
    Javascript
    Bash/Sh

Dependencies:
    python-magic: pip install python-magic
"""

import sys

from parsers import common
from parsers import c_parser as cp
from parsers import go_parser as gp
from parsers import js_parser as jp
from parsers import shell_parser as sp

# MIME_MAP = {
#     'text/x-c': c_parser,               # C
#     'text/x-c++': c_parser,             # C++
#     'text/x-go': go_parser,             # Go
#     'text/x-java-source': c_parser,     # Java
#     'text/x-javascript': js_parser,     # Javascript
#     'text/x-shellscript': shell_parser  # Unix shell
# }


def extract_comments(content, filetype):
    filetype = filetype.lower()
    if filetype in ["c", "cpp", "cc", "java"]:
        return cp.extract_comments(content)
    elif filetype == "go":
        return gp.extract_comments(content)
    elif filetype == "js":
        return jp.extract_comments(content)
    elif filetype == "sh":
        return sp.extract_comments(content)
    else:
        return ["ERROR, unexpected filetype for parser: " + str(filetype)]

if __name__ == '__main__':
    # file_name = "/Users/cbono/Documents/code/codehealth/tests/java/WordCount.java"
    file_name = "/Users/cbono/Documents/code/codehealth/tests/inline-resources.js"
    with open(file_name, "r") as f:
        txt=f.read()
        cs=extract_comments(txt, "java")
        print(cs)
        for c in cs:
            print("comment: " + str(c._text))

# def main(argv):
#     """Extracts comments from files and prints them to stdout."""
#     for filename in argv:
#         try:
#             comments = extract_comments(filename)
#             for comment in comments:
#                 print(comment.text())
#         except Error as exception:
#             sys.stderr.write(str(exception))

# if __name__ == '__main__':
#     main(sys.argv[1:])