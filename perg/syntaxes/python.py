import re
import string

import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from perg.common_checkers import ALL_COMMON
from perg.common_checkers import check_match_re_simple
from perg.syntaxes import Relevance
from perg.syntaxes import PergSyntaxParseError
from perg import Pattern
from perg import Location


PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)


def check_relevance(filename):
    for ext in ('.py', '.pyi', '.pyx'):
        if filename.endswith(ext):
            return Relevance.YES

    # Definitely not Python
    if filename.endswith('.pyc'):
        return Relevance.NO

    return Relevance.MAYBE


def check_match_python_format_str(pattern, s, partial=False):
    regex = ""
    try:
        parsed = list(string.Formatter().parse(pattern))
    except ValueError:
        return False

    for literal_text, field_name, format_spec, conversion in parsed:
        regex += re.escape(literal_text)
        if field_name is not None:
            regex += '.*'

    return check_match_re_simple(regex, s, partial=partial)


def node_to_string(node):
    if node.type == "string":
        if len(node.children) == 2:
            start_quote, end_quote = node.children
            assert start_quote.type == 'string_start'
            assert end_quote.type == 'string_end'
            return ''

        start_quote, content, end_quote = node.children
        return node_to_string(content)

    if node.type != 'string_content':
        raise NotImplementedError(f"dunno how to handle {node.type}")

    chars = list(node.text.decode())

    for escape_sequence in reversed(node.children):
        assert escape_sequence.type == "escape_sequence"
        assert escape_sequence.text.startswith(b"\\")
        text = escape_sequence.text.decode()

        try:
            replacement = {
                 '\\\n': '', # Backslash and newline ignored
                '\\\\': '\\',
                r'\'': '\'',
                r'\"': '\"',
                r'\a': '\a',
                r'\b': '\b',
                r'\f': '\f',
                r'\n': '\n',
                r'\r': '\r',
                r'\t': '\t',
                r'\v': '\v',
            }[text]
        except KeyError:
            if re.match(r'\\[0-7]{1,3}', text):
                replacement = chr(int(text[1:], base=8))
            elif re.match(r'\\x[0-9a-fA-F]{2}', text):
                replacement = chr(int(text[2:], base=16))
            elif re.match(r'\\u[0-9a-fA-F]{4}', text):
                replacement = chr(int(text[2:], base=16))
            elif re.match(r'\\U[0-9a-fA-F]{8}', text):
                replacement = chr(int(text[2:], base=16))
            else:
                raise ValueError("dunno man")

        start = escape_sequence.start_byte - node.start_byte
        end = escape_sequence.end_byte - node.start_byte

        chars[start:end] = replacement

    return ''.join(chars)


class FStringPattern:
    def __init__(self, node):
        self.node = node

    def to_regex(self) -> str:
        regex = ""

        for child in self.node.children:
            if child.type in ('string_start', 'string_end'):
                continue
            elif child.type == 'string_content':
                regex += node_to_string(child)
            elif child.type == 'interpolation':
                regex += '.*'
            else:
                raise NotImplementedError(f"dunno how to handle {child.type}")
        return regex


def check_match_python_f_string(pattern, s, partial):
    return check_match_re_simple(pattern.to_regex(), s, partial)


def parse_node(node, filename):
    if node.type == "string":
        if any([c.type == "interpolation" for c in node.children]):
            yield Pattern(
                location=Location(
                    filename=filename,
                    start_lineno=node.start_point[0] + 1,  # tree-sitter uses 0-indexed lines, where we want 1-indexed.
                    start_col=node.start_point[1],
                    end_lineno=node.end_point[0] + 1,  # tree-sitter uses 0-indexed lines, where we want 1-indexed.
                    end_col=node.end_point[1],
                ),
                value=FStringPattern(node),
                check_fns=(check_match_python_f_string,),
            )
        else:
            yield Pattern(
                location=Location(
                    filename=filename,
                    start_lineno=node.start_point[0] + 1,  # tree-sitter uses 0-indexed lines, where we want 1-indexed.
                    start_col=node.start_point[1],
                    end_lineno=node.end_point[0] + 1,  # tree-sitter uses 0-indexed lines, where we want 1-indexed.
                    end_col=node.end_point[1],
                ),
                value=node_to_string(node),
                check_fns=ALL_COMMON + (check_match_python_format_str,),
            )
    else:
        for child in node.children:
            yield from parse_node(child, filename)


def source_to_node(source):
    tree = parser.parse(source.encode())
    return tree.root_node


def parse(f, filename):
    try:
        source = f.read()
    except UnicodeDecodeError:
        raise PergSyntaxParseError()
    node = source_to_node(source)
    yield from parse_node(node, filename)
