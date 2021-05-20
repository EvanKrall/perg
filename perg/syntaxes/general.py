# A general-purpose string literal finder for perg.

import re
import ast
from perg.common_checkers import check_match_re

def parse(f, filename):
    stringRE = re.compile(r'"(?:\\.|[^"])*"') # Matches double-quoted strings.
    try:
        lines = list(f)
    except UnicodeDecodeError:
        pass
    else:
        for lineno, line in enumerate(lines):
            for match in stringRE.finditer(line.rstrip('\n')):
                literal = line[match.start():match.end()]
                yield (
                    lineno + 1,
                    match.start(),
                    lineno + 1,
                    match.end(),
                    unquote(literal),
                    [check_match_re,],
                )


def unquote(literal):
    return ast.literal_eval(literal)