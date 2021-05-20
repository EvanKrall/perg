import ast
import re
import string


def check_match_re(pattern, s, partial=False):
    if partial:
        return bool(re.search(pattern, s))
    else:
        return bool(re.fullmatch(pattern, s))


def check_match_format_str(pattern, s, partial=False):
    regex = ""
    for literal_text, field_name, format_spec, conversion in string.Formatter().parse(pattern):
        regex += re.escape(literal_text)
        if field_name is not None:
            regex += '.*'

    return check_match_re(regex, s, partial=partial)


ALL_PYTHON_CHECKERS = [check_match_re, check_match_format_str]

class StringFinder(ast.NodeVisitor):
    def __init__(self, found_nodes):
        self.found_nodes = found_nodes

    def visit_JoinedStr(self, node):
        self.found_nodes.append(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            self.found_nodes.append(node)


def parse(f):
    source = f.read()
    lines = source.split('\n')
    tree = ast.parse(''.join(source))

    found_nodes = []
    string_finder = StringFinder(found_nodes)
    string_finder.visit(tree)

    for node in found_nodes:
        literal_lines = lines[node.lineno - 1 : node.end_lineno]
        # trim the last line first in case this is a single-line. If we did this in the opposite order, trimming
        # the beginning of the line would shift the end forward.
        literal_lines[-1] = literal_lines[-1][:node.end_col_offset]
        literal_lines[0] = literal_lines[0][node.col_offset:]
        literal = '\n'.join(literal_lines)

        if isinstance(node, ast.JoinedStr):
            # A bit hacky, but it works lol. This strips the f off the beginning of the source of an f string, and
            # parses it as a regular string.
            value = eval(literal[1:])
        else:
            value = node.value

        yield node.lineno, node.col_offset, value, literal, ALL_PYTHON_CHECKERS
