# A general-purpose string literal finder for perg.

import re
import ast

def parse(f):
        stringRE = re.compile(r'"(?:\\.|[^"])*"') # Matches double-quoted strings.
        for lineno, line in enumerate(f):
            for match in stringRE.finditer(line.rstrip('\n')):
                literal = line[match.start():match.end()]
                yield lineno, match.start(), unquote(literal), literal


def unquote(literal):
    return ast.literal_eval(literal)