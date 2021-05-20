from perg.perg import pattern_is_trivial
from perg.common_checkers import check_match_re_simple

def test_pattern_is_trivial():
	assert check_match_re_simple('.*', '')
	assert check_match_re_simple('.*', 'a')
	assert pattern_is_trivial(check_match_re_simple, '.*')
	assert pattern_is_trivial(check_match_re_simple, r'.?')
	assert not pattern_is_trivial(check_match_re_simple, r'.+')
	assert not pattern_is_trivial(check_match_re_simple, r'\w+')
	assert not pattern_is_trivial(check_match_re_simple, r'\s+')