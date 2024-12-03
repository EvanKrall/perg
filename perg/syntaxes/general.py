# A general-purpose string literal finder for perg.

import re
import ast
from perg.common_checkers import ALL_COMMON
from perg.syntaxes import Relevance
from perg import Pattern
from perg import Location


def check_relevance(filename):
    return Relevance.MAYBE


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
                yield Pattern(
                    location=Location(
                        filename=filename,
                        start_lineno=lineno + 1,
                        start_col=match.start(),
                        end_lineno=lineno + 1,
                        end_col=match.end(),
                    ),
                    value=unquote(literal),
                    check_fns=ALL_COMMON,
                )


def unquote(literal):
    return ast.literal_eval(literal)