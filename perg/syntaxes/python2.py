import ast


def parse(f):
    tree = ast.parse(''.join(f))
    for node in ast.walk(tree):
        if isinstance(node, ast.Str):
            # the last thing yielded is really unfortunate, since it's not
            # going to be the literal representation in the source code.
            yield node.lineno, node.col_offset, node.s, repr(node.s)
