from perg import heuristics
from perg.common_checkers import check_match_re_simple


def test_pattern_matches_empty():
    assert heuristics.pattern_matches_empty(check_match_re_simple, '.*')
    assert heuristics.pattern_matches_empty(check_match_re_simple, r'.?')
    assert not heuristics.pattern_matches_empty(check_match_re_simple, r'.+')
    assert not heuristics.pattern_matches_empty(check_match_re_simple, r'\w+')
    assert not heuristics.pattern_matches_empty(check_match_re_simple, r'\s+')


def test_deletable_chars_1():
    pattern = "foo .* baz"
    text = "foo bar baz"
    deletable = heuristics.deletable_chars(check_match_re_simple, pattern, text, partial=False)
    assert deletable == [4,5,6]


def test_deletable_chars_2():
    pattern = "foo .a?. baz"
    text = "foo bar baz"
    deletable = heuristics.deletable_chars(check_match_re_simple, pattern, text, partial=False)
    # When deleting b, then `ar` each match the dots in `.a?.` and the a? matches nothing
    # When deleting z, then `ba` each match the dots in `.a?.` and the a? matches nothing
    assert deletable == [4,5,6]


def test_deletable_chars_3():
    pattern = "foo ba?r baz"
    text = "foo bar baz"
    deletable = heuristics.deletable_chars(check_match_re_simple, pattern, text, partial=False)
    assert deletable == [5]


def test_deletable_chars_4():
    pattern = "foo [^a]a?[^a] baz"
    text = "foo bar baz"
    deletable = heuristics.deletable_chars(check_match_re_simple, pattern, text, partial=False)
    assert deletable == [5]


def test_deletable_chars_5():
    pattern = "foo.*?ba"
    text = "foo bar baz foo bar baz foo bar baz"
    assert check_match_re_simple(pattern, text, partial=True).spans == (
        (0, 6),
        (12, 18),
        (24, 30),
    )

    deletable = heuristics.deletable_chars(check_match_re_simple, pattern, text, partial=True)
    # Only the spaces between foo and bar should be deletable.
    assert deletable == [3, 15, 27]
    # Even though we'd still find 3 occurrences of the pattern in the text if we deleted e.g. the `a` in the first `bar`.
    # We consider a character deletable if it results in an "equivalent" span
    # -- that is, one where the start/end are within 1 character of the original span.
    assert check_match_re_simple(pattern, "foo br baz foo bar baz foo bar baz", partial=True).spans == (
        (0, 9),  # This span is not equivalent to the previous.
        (11, 17),  # This span is not considered when modifying the first bar, since it doesn't include the first bar.
        (23, 29),  # This span is not considered when modifying the first bar, since it doesn't include the first bar.
    )


def test_replaceable_chars_1():
    pattern = "foo .* baz"
    text = "foo bar baz"
    replaceable = heuristics.replaceable_chars(check_match_re_simple, pattern, text, partial=False)
    assert replaceable == [4,5,6]


def test_replaceable_chars_2():
    pattern = "foo .a?. baz"
    text = "foo bar baz"
    replaceable = heuristics.replaceable_chars(check_match_re_simple, pattern, text, partial=False)
    assert replaceable == [4,6]


def test_replaceable_chars_3():
    pattern = "foo ba?r baz"
    text = "foo bar baz"
    replaceable = heuristics.replaceable_chars(check_match_re_simple, pattern, text, partial=False)
    assert replaceable == []
