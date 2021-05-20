import textwrap
from perg.syntaxes import python
from io import StringIO

def test_parse_single_line():
    source = textwrap.dedent("""
        my_cool_regex = "foo .* bar"
    """)

    (lineno, col_offset, text, literal, checkers), = list(python.parse(StringIO(source)))
    assert lineno == 2
    assert col_offset == 16
    assert text == "foo .* bar"
    assert literal == '"foo .* bar"'


def test_parse_multi_line():
    source = textwrap.dedent('''
        my_cool_multiline_regex = """foo
        .*
        bar"""
    ''')

    (lineno, col_offset, text, literal, checkers), = list(python.parse(StringIO(source)))
    assert lineno == 2
    assert col_offset == 26
    assert text == "foo\n.*\nbar"
    assert literal == '"""foo\n.*\nbar"""'
