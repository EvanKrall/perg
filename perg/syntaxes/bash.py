import shlex

import tree_sitter_bash
from tree_sitter import Language, Parser

from perg.common_checkers import check_match_re_simple
from perg.common_checkers import check_match_re_verbose
from perg.common_checkers import check_shell_glob
from perg.syntaxes import Relevance
from perg.syntaxes import PergSyntaxParseError
from perg import Pattern
from perg import Location


BASH_LANGUAGE = Language(tree_sitter_bash.language())
parser = Parser(BASH_LANGUAGE)


def print_example_tree():
    source = open('test_inputs/shell.sh').read()
    tree = parser.parse(source.encode())
    root_node = tree.root_node
    def print_node(node, indent=0):
        start_line, start_col = node.start_point
        end_line, end_col = node.end_point
        print(
            ' ' * indent +
            f"{node.type} "
            f"({start_line + 1}:{start_col} - "
            f"{end_line + 1}:{end_col})  -- "
            f"{node.text.decode()!r}"
        )

        for child in node.children:
            print_node(child, indent + 4)
    print_node(root_node)


def check_relevance(filename):
    if filename.endswith('.sh'):
        return Relevance.YES
    else:
        return Relevance.MAYBE


WILDCARD = object()


def regexes_from_node(node, filename):
    """Recursively parse a tree-sitter node and return a list of [literal strings or WILDCARD].

    Convert strings into regexes, replacing variables with WILDCARD and escaping special characters.
    For example, the bash string "foo $a baz" would yield ['foo ', WILDCARD, ' baz'].
    """
    if node.type in ('word', 'raw_string', 'extglob_pattern', 'ansi_c_string'):
        value, = shlex.split(node.text.decode())
        return [value]
    elif node.type == "heredoc_content" or (node.type == "heredoc_body" and not node.children):
        # a heredoc_body with no children is when the terminator is quoted, e.g. <<'EOF'
        # in this case, we treat it similarly to heredoc_content.
        return [node.text.decode()]
    elif node.type in ("expansion", "simple_expansion", "command_substitution"):
        return [WILDCARD]
    elif node.type == "string_content":
        value, = shlex.split('"' + node.text.decode() + '"')
        return [value]
    elif node.type in ("string", "heredoc_body", "concatenation"):
        regex_parts_unescaped = []
        for child in node.children:
            regex_parts = regexes_from_node(child, filename)
            regex_parts_unescaped.extend(regex_parts)
        return regex_parts_unescaped
    elif node.type in ('"',):
        return []
    else:
        breakpoint()
        raise ValueError(f"Unknown node type: {node.type}")


def parse_node(node, filename):
    """Wrap regexes from regexes_from_node in Pattern objects."""
    if node.type in ('word', 'raw_string', 'extglob_pattern', 'ansi_c_string', 'string', 'heredoc_body', 'concatenation'):
        regex_parts = regexes_from_node(node, filename)
        for check_fn, wildcard_value in (
            (check_match_re_simple, '.*'),
            (check_match_re_verbose, '.*'),
            (check_shell_glob, '*'),
        ):
            regex = ''.join(
                part if part is not WILDCARD else wildcard_value
                for part in regex_parts
            )

            yield Pattern(
                location=Location(
                    filename=filename,
                    start_lineno=node.start_point[0] + 1,
                    start_col=node.start_point[1],
                    end_lineno=node.end_point[0] + 1,
                    end_col=node.end_point[1],
                ),
                value=regex,
                check_fns=(check_fn,),
            )

            # If the regex contains a newline, yield a Pattern for each line.
            if '\n' in regex:
                for line in regex.split('\n'):
                    yield Pattern(
                        location=Location(
                            # TODO: this location is arguably not correct -- this will show e.g. the entire heredoc, rather than the single line within the heredoc.
                            filename=filename,
                            start_lineno=node.start_point[0] + 1,
                            start_col=node.start_point[1],
                            end_lineno=node.end_point[0] + 1,
                            end_col=node.end_point[1],
                        ),
                        value=line,
                        check_fns=(check_fn,),
                    )
    elif hasattr(node, 'children') and node.children:
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

if __name__ == '__main__':
    print_example_tree()
