import re
import itertools
from functools import reduce


def check_match_re(pattern, s, partial=False, ignore_case=False):
    flags = [
        [re.MULTILINE],
        [re.DOTALL],
        [re.VERBOSE, 0],
    ]
    if ignore_case:
        flags.append([re.IGNORE_CASE])

    for flag_combo in itertools.product(*flags):
        try:
            compiled = re.compile(
                pattern,
                reduce(lambda a, b: a | b, flag_combo)
            )
        except re.error:
            continue

        method = re.search if partial else re.fullmatch
        if method(compiled, s):
            return True

    return False
