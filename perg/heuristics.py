
def pattern_matches_empty(check_fn, pattern):
    """This tests a pattern against the empty string. Example patterns that would match this:
        '.*'
        ''
    """
    return check_fn(pattern, '', partial=-1)


def pattern_matches_single_char(check_fn, pattern):
    """This tests a pattern against each of the first 255 characters except newline. If all of
    them match, the pattern is considered trivial. Example patterns that would match this:
        .*
        .?
        .+
    """
    test_strings = [chr(c) for c in range(1, 255) if chr(c) != '\n']
    return all([check_fn(pattern, ts, partial=-1) for ts in test_strings])


def too_many_things_deletable(check_fn, pattern, s, max_deletable=-1, min_undeletable=0):
    deletable = 0
    required = 0

    for i, char in enumerate(s):
        if check_fn(pattern, s[:i] + s[i+1:]):
            # print(f"s[{i}] ({s[i]!r}) is deletable in pattern {pattern!r} with checker {check_fn.__name__}")
            deletable += 1
        else:
            required += 1

    if max_deletable >= 0 and deletable > max_deletable:
        return True

    if required < min_undeletable:
        return True

    return False
