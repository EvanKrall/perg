import math

def pattern_matches_empty(match):
    """This tests a pattern against the empty string. Example patterns that would match this:
        '.*'
        ''
    """
    return match.check_fn(match.pattern.value, '', partial=-1)


def pattern_matches_single_char(match):
    """This tests a pattern against each of the first 255 characters except newline. If all of
    them match, the pattern is considered trivial. Example patterns that would match this:
        .*
        .?
        .+
    """
    test_strings = [chr(c) for c in range(1, 255) if chr(c) != '\n']
    return all(match.check_fn(match.pattern.value, ts, partial=-1) for ts in test_strings)


def too_many_things_deletable(match, max_deletable=-1, min_undeletable=0):
    deletable_indexes = deletable_chars(match)
    deletable = len(deletable_indexes)
    required = len(match.text) - deletable

    if max_deletable >= 0 and deletable > max_deletable:
        return True

    if required < min_undeletable:
        return True

    return False


def deletable_chars(match):
    return replaceable_chars(match, replacement_candidates=('',))


def spans_are_equivalent(span1, span2, deletion=False):
    start1, end1 = span1
    start2, end2 = span2
    if deletion:
        return (start1 - 1 <= start2 <= start1 + 1) and (end1 - 1 <= end2 <= end1 + 1)
    else:
        return span1 == span2


ONE_BYTE_CHARS = tuple(chr(c) for c in range(1, 255) if chr(c) != '\n')


def replaceable_chars(match, replacement_candidates=ONE_BYTE_CHARS):
    replaceable_indexes = []
    for span in match.result.spans:
        for i in range(span[0], span[1]):
            for replacement in find_replacement_alphabet_for_position(match, span, i, replacement_candidates):
                if match.text[i] == replacement:
                    continue

                replaceable_indexes.append(i)
                break

    return replaceable_indexes


def find_replacement_alphabet_for_position(match, span, i, replacement_candidates):
    for replacement in replacement_candidates:
        modified_text = match.text[:i] + replacement + match.text[i+1:]
        # print(f"testing {modified_text!r} against {pattern}")
        result = match.check_fn(match.pattern.value, modified_text, match.partial)
        # TODO: maybe I should check if there's an "equivalent" span in the new results? Something that covers the same characters as the span we're currently modifying.
        # print(result)
        if result and any(spans_are_equivalent(new_span, span, deletion=(replacement == '')) for new_span in result.spans):
            yield replacement


def information(match):
    r"""
    From https://en.wikipedia.org/wiki/Entropy_(information_theory):

    > we can define the information, or surprisal, of an event E by
    > I(E) = -log2(p(E))

    This heuristic estimates the amount of information needed to express the text given the pattern.
    I.e. if you were to try and send a message "foo bar baz" to your friend, and your friend already
    knows that the message matches the regex "foo .* baz", all you really need to send is "bar".

    This requires you to send less information than if your friend only knows that the string
    matches "foo .*", or worse yet, ".*"

    We then subtract this from the size of your text (assuming 8 bits per char), to determine how
    much information the pattern gives you about the string.

    Under this heuristic, more specific patterns should yield higher scores than less-specific
    patterns.

    "[a-z]+ [a-z]+ [a-z]+" is more specific than ".+ .+ .+"

    To estimate this, we iterate over each character in our text and determine the valid
    replacements for that character (including deletion).
    (We only look at unicode characters between 1 and 254, since in most cases it seems unnecessary
    to enumerate every valid Unicode character.)
    Once we have the size of the valid alphabet (+1 for if deletion), we assume that the the
    probability of seeing the character that we actually saw is 1/alphabet_size.

    If we can't find a valid replacement (the character that we have is the only character that's
    valid in that location), the probability is 1 and the information gained is 0 bits.

    If the character can be replaced by any single byte character (but not deleted), the information
    gained is log2(255) = 7.99 bits, so the pattern '.' provides 0.01 bits of information.

    If the character can only be replaced by a decimal digit, the information gained is log2(10) ~=
    3.32 bits, so '\d' or '[0-9]' provides 4.68 bits.

    Alphanumeric would be log2(2*26 + 10) ~= 5.95 bits, meaning the pattern provides 2.05 bits.

    This is going to miss a lot of nuance about regexes.
    Given the "foo .* baz"/"foo bar baz" example, we essentially are going to experimentally
    determine that the pattern is roughly "foo .?.?.? baz" -- that each of the characters "bar" in
    "foo bar baz" are replaceable with any other character (with a unicode value below 255) or
    deletable without causing the pattern to stop matching the text.

    We could instead use a library like https://github.com/qntm/greenery and do something smarter,
    like walking through the DFA and, at each step, determining the size of the character class that
    would take us to the same next state as our actual string does. Or perhaps modify greenery's
    cardinality method (which raises OverflowError if the regex matches an infinite number of
    strings) so you could ask it how many strings N of (<=) length K could match the regex; then
    use log2(N) from there.

    However, this approach would restrict us to the subset of regexes that greenery supports --
    notably, it doesn't support the non-regular features that many regex libraries (including
    python's re module) support; nor does it support named capture groups.

    By doing it experimentally, we should be able to support any pattern-matching library, at the
    cost of some accuracy for this heuristic.

    TODO: this will treat backreferences as too specific.
    The pattern '(.*)\1' would match the string 'abcabc' but not the string '_bcabc', 'a_cabc',
    'ab_abc', and so on; this means we will assume that all 6 characters in the string are
    irreplaceable, so the information returned would be 0, as if the pattern had been 'abcabc'.

    TODO: lookahead/lookbehinds would be handled incorrectly, as we assume that anything outside of
    the matched span is replaceable.
    """

    information_bits = 0
    end_of_last_span = 0

    for span in match.result.spans:
        start, end = span
        # If there's anything outside a span, it means we're doing partial matches
        # and therefore it's equivalent to .* -- anything outside the match doesn't matter.
        information_bits += 8 * (start - end_of_last_span)
        end_of_last_span = end

        for i in range(start, end):
            count = len(
                list(
                    find_replacement_alphabet_for_position(
                        match=match,
                        span=span,
                        i=i,
                        replacement_candidates=[chr(c) for c in range(1, 256)] + [''],
                    )
                )
            )
            information_bits += math.log2(count)

    information_bits += 8 * (len(match.text) - end_of_last_span)

    return len(match.text) * 8 - information_bits
