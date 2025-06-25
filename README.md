# perg: like grep, but backwards

grep finds all the strings in your files that match a given pattern.

perg finds all the patterns in your files that match a given string.

Patterns may be regexes, globs, or other pattern-matching languages.
Patterns may also be format strings or templates.

## Examples

### Webapp routes

Ever forget where you defined the route that handles that URL?

```python
@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}
```

`perg '/items/12345'` would find the `@app.get` line.

### Log entries

Trying to figure out where that log line comes from?

`perg "User Alice performed a login action."` would find this code:

```python
logging.info(f"User {user} performed a {action} action.")
```

## Won't this just find every `.*`, `.`, `%`, or  `*` in the codebase?

By default, `perg` uses simple heuristics to ignore matches where the pattern would also match the empty string or any single byte.
This gets rid of most of the pointless matches.

Additionally, for each match, `perg` attempts various edits to your test string to decide how much information in your test string is implied by the pattern.

For the string `foo bar baz`, the following regexes are sorted from most to least informative:

- `foo bar baz`
- `foo [a-z]* baz`
- `foo [a-zA-Z]* baz`
- `foo .* baz`
- `foo .*`
- `...........`
- `.*`

Anything that scores worse than 50% as strict as the best match is hidden by default.
This threshold can be adjusted with `--pct-of-best-score`, and this behavior can be disabled entirely with `--no-score-by-information`.

(Additional details can be seen in the docstring for `information()` in heuristics.py.)

# Language support

For each programming language perg supports, there is a module in `syntaxes/`.

Currently supported languages:

- python

Each syntax module must have a method `parse(f, filename)`.
This method will be passed the file object and filename of each source file.
It should return an iterator of `Pattern` objects.

A `Pattern` object contains:

- The location of the pattern (filename, starting & ending line numbers and columns)
- A set of check functions which determine whether the given string matches the pattern.

This allows a single pattern to be checked against several different pattern languages.
For example, a string literal found in your source code could be tested as a format string, a regex, a glob, a SQL pattern, and for string equality.
