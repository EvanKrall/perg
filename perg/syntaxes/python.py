import ast
import re
import string
from perg.common_checkers import check_match_re


def check_match_format_str(pattern, s, partial=False):
    regex = ""
    for literal_text, field_name, format_spec, conversion in string.Formatter().parse(pattern):
        regex += re.escape(literal_text)
        if field_name is not None:
            regex += '.*'

    return check_match_re(regex, s, partial=partial)


class StringFinder(ast.NodeVisitor):
    def __init__(self, found_nodes):
        self.found_nodes = found_nodes

    def visit_JoinedStr(self, node):
        self.found_nodes.append(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            self.found_nodes.append(node)


def parse(f, filename):
    source = f.read()
    try:
        tree = ast.parse(''.join(source))
    except (SyntaxError, UnicodeDecodeError):
        return

    found_nodes = []
    string_finder = StringFinder(found_nodes)
    string_finder.visit(tree)

    for node in found_nodes:
        if isinstance(node, ast.JoinedStr):
            # A bit hacky, but it works lol. This strips the f off the beginning of the source of an f string, and
            # parses it as a regular string.
            value = ast.literal_eval(ast.unparse(node)[1:])
        else:
            value = node.value

        yield (
            node.lineno,
            node.col_offset,
            node.end_lineno,
            node.end_col_offset,
            value,
            [check_match_re, check_match_format_str],
        )
