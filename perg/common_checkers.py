import re
import itertools
from functools import reduce


def check_match_re(pattern, s, partial=False, ignore_case=False):
    flag_combos = [
        [re.MULTILINE],
        [re.DOTALL],
        [re.VERBOSE, 0],
    ]
    if ignore_case:
        flag_combos.append([re.IGNORE_CASE])

    for flag_combo in itertools.product(*flag_combos):
        flags = reduce(lambda a, b: a | b, flag_combo)
        if check_match_re_simple(pattern, s, partial=partial, flags=flags):
            return True
    return False


def check_match_re_simple(pattern, s, partial=False, flags=0):
    try:
        compiled = re.compile(pattern, flags)
    except re.error:
        return False

    method = re.search if partial else re.fullmatch
    return method(compiled, s)
