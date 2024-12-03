from perg.heuristics import pattern_matches_empty
from perg.common_checkers import check_match_re_simple

def pattern_matches_empty():
	assert pattern_matches_empty(check_match_re_simple, '.*')
	assert pattern_matches_empty(check_match_re_simple, r'.?')
	assert not pattern_matches_empty(check_match_re_simple, r'.+')
	assert not pattern_matches_empty(check_match_re_simple, r'\w+')
	assert not pattern_matches_empty(check_match_re_simple, r'\s+')