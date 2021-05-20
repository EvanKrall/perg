import re
import fnmatch


ALL_COMMON = []
RE_FLAGS = re.MULTILINE | re.DOTALL


def common_checker(check_fn):
    ALL_COMMON.append(check_fn)
    return check_fn



@common_checker
def check_match_re_verbose(pattern, s, partial=False):
    return check_match_re_simple(pattern, s, partial=partial, flags=RE_FLAGS | re.VERBOSE)


@common_checker
def check_match_re_simple(pattern, s, partial=False, flags=RE_FLAGS):
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
