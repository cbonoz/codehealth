       

import common            

def parse_code(text):
    try:
        state = 0
        current_comment = ''
        comments = []
        line_counter = 1
        comment_start = 1
        for char in text:
            if not char:
                if state is 3 or state is 4:
                    raise common.UnterminatedCommentError()
                if state is 2:
                    # Was in single line comment. Create comment.
                    comment = common.Comment(current_comment, line_counter)
                    comments.append(comment)
                return comments
            if state is 0:
                # Waiting for comment start character or beginning of
                # string.
                if char == '/':
                    state = 1
                elif char == '"':
                    state = 5
            elif state is 1:
                # Found comment start character, classify next character and
                # determine if single or multiline comment.
                if char == '/':
                    state = 2
                elif char == '*':
                    comment_start = line_counter
                    state = 3
                else:
                    state = 0
            elif state is 2:
                # In single line comment, read characters until EOL.
                if char == '\n':
                    comment = common.Comment(current_comment, line_counter)
                    comments.append(comment)
                    current_comment = ''
                    state = 0
                else:
                    current_comment += char
            elif state is 3:
                # In multi-line comment, add characters until '*'
                # encountered.
                if char == '*':
                    state = 4
                else:
                    current_comment += char∏
            elif state is 4:
                # In multi-line comment with asterisk found. Determine if
                # comment is ending.
                if char == '/':
                    comment = common.Comment(
                        current_comment, comment_start, multiline=True)
                    comments.append(comment)
                    current_comment = ''
                    state = 0
                else:
                    current_comment += '*'
                    # Care for multiple '*' in a row
                    if char != '*':
                        current_comment += char
                        state = 3
            elif state is 5:
                # In string literal, expect literal end or escape char.
                if char == '"':
                    state = 0
                elif char == '\\':
                    state = 6
            elif state is 6:
                # In string literal, escaping current char.
                state = 5
            if char == '\n':
                line_counter += 1
    except OSError as exception:
        raise common.FileError(str(exception))

