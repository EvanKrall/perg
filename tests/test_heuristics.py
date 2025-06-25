import math
from perg import heuristics
from perg import Pattern
from perg import Match
from perg import Location
from perg.common_checkers import check_match_re_simple

def make_pattern(regex):
    return Pattern(
        location=Location(
            filename="/dev/null",
            start_lineno=1,
            start_col=0,
            end_lineno=1,
            end_col=len(regex),
        ),
        value=regex,
        check_fns=(check_match_re_simple,),
    )

def make_match(
    pattern: str,
    text: str,
    check_fn=check_match_re_simple,
    partial=False,
):
    return Match(
        check_fn=check_fn,
        pattern=make_pattern(pattern),
        text=text,
        partial=partial,
    )


def test_pattern_matches_empty():
    assert heuristics.pattern_matches_empty(make_match('.*', 'doesntmatter'))
    assert heuristics.pattern_matches_empty(make_match(r'.?', 'doesntmatter', partial=1))
    assert not heuristics.pattern_matches_empty(make_match(r'.+', 'doesntmatter'))
    assert not heuristics.pattern_matches_empty(make_match(r'\w+', 'doesntmatter'))
    assert not heuristics.pattern_matches_empty(make_match(r'\s+', ' '))


def test_deletable_chars_1():
    match = make_match(
        pattern="foo .* baz",
        text="foo bar baz",
    )
    deletable = heuristics.deletable_chars(match)
    assert deletable == [4,5,6]


def test_deletable_chars_2():
    match = make_match(
        pattern="foo .a?. baz",
        text="foo bar baz",
    )
    deletable = heuristics.deletable_chars(match)
    # When deleting b, then `ar` each match the dots in `.a?.` and the a? matches nothing
    # When deleting z, then `ba` each match the dots in `.a?.` and the a? matches nothing
    assert deletable == [4,5,6]


def test_deletable_chars_3():
    match = make_match(
        pattern="foo ba?r baz",
        text="foo bar baz",
    )
    deletable = heuristics.deletable_chars(match)
    assert deletable == [5]


def test_deletable_chars_4():
    match = make_match(
        pattern="foo [^a]a?[^a] baz",
        text="foo bar baz",
    )
    deletable = heuristics.deletable_chars(match)
    assert deletable == [5]


def test_deletable_chars_5():
    match = make_match(
        pattern="foo.*?ba",
        text="foo bar baz foo bar baz foo bar baz",
        partial=True,
    )
    assert match.result.spans == (
        (0, 6),
        (12, 18),
        (24, 30),
    )

    deletable = heuristics.deletable_chars(match)
    # Only the spaces between foo and bar should be deletable.
    # TODO: should characters between spans count as deletable?
    assert deletable == [3, 15, 27]
    # Even though we'd still find 3 occurrences of the pattern in the text if we deleted e.g. the `a` in the first `bar`.
    # We consider a character deletable if it results in an "equivalent" span
    # -- that is, one where the start/end are within 1 character of the original span.
    assert check_match_re_simple(match.pattern.value, "foo br baz foo bar baz foo bar baz", partial=True).spans == (
        (0, 9),  # This span is not equivalent to the previous.
        (11, 17),  # This span is not considered when modifying the first bar, since it doesn't include the first bar.
        (23, 29),  # This span is not considered when modifying the first bar, since it doesn't include the first bar.
    )


def test_replaceable_chars_1():
    match = make_match(
        pattern="foo .* baz",
        text="foo bar baz",
    )
    replaceable = heuristics.replaceable_chars(match)
    assert replaceable == [4,5,6]


def test_replaceable_chars_2():
    match = make_match(
        pattern="foo .a?. baz",
        text="foo bar baz",
    )
    replaceable = heuristics.replaceable_chars(match)
    assert replaceable == [4,6]


def test_replaceable_chars_3():
    match = make_match(
        pattern="foo ba?r baz",
        text="foo bar baz",
    )
    replaceable = heuristics.replaceable_chars(match)
    assert replaceable == []

def test_replaceable_chars_4():
    match = make_match(
        pattern=".oo bar ba.",
        text="foo bar baz",
    )
    replaceable = heuristics.replaceable_chars(match)
    assert replaceable == [0, 10]


def test_information_dotstar():
    match = make_match(
        pattern=".*",
        text="foo bar baz"
    )
    information = heuristics.information(match)
    assert information == 0

def test_information_prefix_suffix():
    match = make_match(
        pattern="foo .* baz",
        text="foo bar baz",
    )
    information = heuristics.information(match)
    expected_information = 8 * len('foo  baz')
    assert -0.01 <= (expected_information - information) <= 0.01

def test_information_charclass():
    match = make_match(
        pattern="foo [a-z]* baz",
        text="foo bar baz",
    )
    information = heuristics.information(match)
    expected_information = 8 * len(match.text) - (math.log2(27)) * len("bar")  # 27 = 26 for the alphabet and 1 for deletion
    assert -0.01 <= (expected_information - information) <= 0.01
