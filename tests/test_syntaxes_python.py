import textwrap
from perg.syntaxes import python
from io import StringIO

def test_parse_single_line():
    source = textwrap.dedent("""
        my_cool_regex = "foo .* bar"
    """)

    results = list(python.parse(StringIO(source), 'source.py'))
    pattern = results[0]
    assert pattern.location.start_lineno == 2
    assert pattern.location.start_col == 16
    assert pattern.location.end_lineno == 2
    assert pattern.location.end_col == 28
    assert pattern.value == "foo .* bar"


def test_parse_multi_line():
    source = textwrap.dedent('''
        my_cool_multiline_regex = """foo
        .*
        bar"""
    ''')

    (pattern,) = list(python.parse(StringIO(source), 'source.py'))
    assert pattern.location.start_lineno == 2
    assert pattern.location.start_col == 26
    assert pattern.location.end_lineno == 4
    assert pattern.location.end_col == 6
    assert pattern.value == "foo\n.*\nbar"


def test_node_to_string():
    def source_to_node_to_text(text):
        return python.node_to_string(python.source_to_node(text).children[0].children[0])
    assert source_to_node_to_text('"x \\\n y"') == "x  y"
    assert source_to_node_to_text("\"hi \\\" hello\"") == "hi \" hello"
    assert source_to_node_to_text(r'"x \x64 y"') == 'x \x64 y'
    assert source_to_node_to_text(r'"x \234 y"') == 'x \234 y'
    assert source_to_node_to_text(r'"x \u1234 y"') == 'x \u1234 y'
    assert source_to_node_to_text(r'"x \U00000020 y"') == 'x \U00000020 y'
