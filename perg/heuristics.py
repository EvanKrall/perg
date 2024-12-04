
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


def too_many_things_deletable(check_fn, pattern, s, partial, max_deletable=-1, min_undeletable=0):
    deletable_indexes = deletable_chars(check_fn, pattern, s, partial)
    deletable = len(deletable_indexes)
    required = len(s) - deletable

    if max_deletable >= 0 and deletable > max_deletable:
        return True

    if required < min_undeletable:
        return True

    return False


def deletable_chars(check_fn, pattern, s, partial):
    return replaceable_chars(check_fn, pattern, s, partial, replacement_candidates=('',))


def spans_are_equivalent(span1, span2, deletion=False):
    start1, end1 = span1
    start2, end2 = span2
    if deletion:
        return (start1 - 1 <= start2 <= start1 + 1) and (end1 - 1 <= end2 <= end1 + 1)
    else:
        return span1 == span2


def replaceable_chars(check_fn, pattern, text, partial, replacement_candidates=tuple(chr(c) for c in range(1, 255) if chr(c) != '\n')):
    replaceable_indexes = []
    original_result = check_fn(pattern, text, partial)
    for span in original_result.spans:
        for i in range(span[0], span[1]):
            # print(f"i={i}, span={span}")
            for replacement in replacement_candidates:
                if text[i] == replacement:
                    continue

                modified_text = text[:i] + replacement + text[i+1:]
                # print(f"testing {modified_text!r} against {pattern}")
                result = check_fn(pattern, modified_text, partial)
                # TODO: maybe I should check if there's an "equivalent" span in the new results? Something that covers the same characters as the span we're currently modifying.
                # print(result)
                if result and any(spans_are_equivalent(new_span, span, deletion=(replacement == '')) for new_span in result.spans):
                    replaceable_indexes.append(i)
                    break
    return replaceable_indexes