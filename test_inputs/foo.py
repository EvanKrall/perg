greedy = "foo .* baz"
non_greedy = "foo .*? baz"

neat_regex = ".*"

bar = "hi"
r_string = r"foo .* baz"
format_string = f"foo {bar} baz"
thing = 5

multiline_string = """
foo
.*
baz
"""

verbose_regex = r"""
    foo # a comment
    .*  # another comment
    baz # a third comment
"""

concatenated_string = (
    "hi hello"
    " this will be a single string"
)

more_specific_regex = "foo .a?. baz"
more_specific_regex = "foo .a. baz"

url_route = r"/api/v1/action/(?P<thing>[^/]*[a-f0-9]{5})"