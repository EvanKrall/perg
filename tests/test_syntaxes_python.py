import textwrap
from perg.syntaxes import python
from io import StringIO

def test_parse_single_line():
    source = textwrap.dedent("""
        my_cool_regex = "foo .* bar"
    """)

    (start_lineno, start_col, end_lineno, end_col, pattern, check_fns), = list(python.parse(StringIO(source), 'source.py'))
    assert start_lineno == 2
    assert start_col == 16
    assert end_lineno == 2
    assert end_col == 28
    assert pattern == "foo .* bar"


def test_parse_multi_line():
    source = textwrap.dedent('''
        my_cool_multiline_regex = """foo
        .*
        bar"""
    ''')

    (start_lineno, start_col, end_lineno, end_col, pattern, check_fns), = list(python.parse(StringIO(source), 'source.py'))
    assert start_lineno == 2
    assert start_col == 26
    assert end_lineno == 4
    assert end_col == 6
    assert pattern == "foo\n.*\nbar"
