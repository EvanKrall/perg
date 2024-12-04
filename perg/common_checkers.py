import re
import fnmatch
from typing import Optional

from perg import CheckResult
from perg import debug

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
        spans = []
        for match in re.finditer(compiled, s):
            if len(match.group(0)) >= partial:
                spans.append(match.span())

        if spans:
            return CheckResult(text=s, spans=tuple(spans))
        else:
            return None
    else:
        if match := re.fullmatch(compiled, s):
            return CheckResult(text=s, spans=(match.span()))
        else:
            return None


@common_checker
def check_string_match(pattern, s, partial) -> Optional[CheckResult]:
    if partial >= 0:
        if len(pattern) < partial:
            return None

        spans = []

        start = 0
        while True:
            start = s.find(pattern, start)
            if start == -1:
                break
            end = start + len(pattern)
            spans.append((start, end))
            start += 1

        if spans:
            return CheckResult(text=s, spans=tuple(spans))
        else:
            return None
    else:
        if pattern == s:
            return CheckResult(text=s, spans=((0, len(s)),))
        return None

@common_checker
def check_shell_glob(pattern, s, partial) -> Optional[CheckResult]:
    regex = fnmatch.translate(pattern)
    debug(f"pattern: {pattern}, regex: {regex}")
    return check_match_re_simple(regex, s, partial=partial)


ALL_COMMON = tuple(ALL_COMMON)