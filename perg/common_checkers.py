import re
import itertools
import fnmatch
from functools import reduce


ALL_COMMON = []


def common_checker(check_fn):
    ALL_COMMON.append(check_fn)
    return check_fn


@common_checker
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


@common_checker
def check_string_match(pattern, s, partial=False):
    if partial:
        return pattern in s
    else:
        return pattern == s


@common_checker
def check_shell_glob(pattern, s, partial=False):
    regex = fnmatch.translate(pattern)
    return check_match_re_simple(regex, s, partial=partial)
