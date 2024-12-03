import re
import fnmatch
from typing import Optional

from perg import CheckResult

ALL_COMMON = []
RE_FLAGS = re.MULTILINE | re.DOTALL


def common_checker(check_fn):
    ALL_COMMON.append(check_fn)
    return check_fn



@common_checker
def check_match_re_verbose(pattern, s, partial) -> Optional[CheckResult]:
    return check_match_re_simple(pattern, s, partial=partial, flags=RE_FLAGS | re.VERBOSE)


@common_checker
def check_match_re_simple(pattern, s, partial, flags=RE_FLAGS) -> Optional[CheckResult]:
    try:
        compiled = re.compile(pattern, flags)
    except re.error:
        return None

    if partial >= 0:
        re_search_or_fullmatch = re.search
    else:
        re_search_or_fullmatch = re.fullmatch

    if match := re_search_or_fullmatch(compiled, s):
        if len(match.group(0)) >= partial:
            return CheckResult(text=s, span=match.span())
        else:
            return None


@common_checker
def check_string_match(pattern, s, partial) -> Optional[CheckResult]:
    if partial >= 0:
        if len(pattern) < partial:
            return None

        start = s.find(pattern)
        if start == -1:
            return None

        end = start + len(pattern)
        return CheckResult(text=s, span=(start, end))
    else:
        if pattern == s:
            return CheckResult(text=s, span=(0, len(s)))
        return None

@common_checker
def check_shell_glob(pattern, s, partial) -> Optional[CheckResult]:
    regex = fnmatch.translate(pattern)
    return check_match_re_simple(regex, s, partial=partial)


ALL_COMMON = tuple(ALL_COMMON)