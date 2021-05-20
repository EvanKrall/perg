import argparse
import os.path
import os
import pkgutil
import importlib
import perg.syntaxes


def find_files(paths, ignore_dot=True):
    """Find all the filenames described by self.paths, open them, and yield them and the syntax associated with them"""
    #TODO recursive (-r)
    for path in paths:
        if os.path.isdir(path):
            for root, subdirs, files in os.walk(path):
                if ignore_dot:
                    for subdir in subdirs:
                        if subdir.startswith('.'):
                            subdirs.remove(subdir)
                for file in files:
                    if not (ignore_dot and file.startswith('.')):
                        newpath = os.path.join(root, file)
                        yield newpath
        else:
            yield path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('text', type=str, help="The text to match patterns against.")
    parser.add_argument('paths', nargs='*', type=str, default=['.'])
    parser.add_argument(
        '--ignore-trivial-match',
        action=argparse.BooleanOptionalAction,
        help="Ignore patterns that match every string.",
        default=True,
    )

    return parser.parse_args()


def find_syntaxes():
    for _, name, _ in pkgutil.iter_modules(perg.syntaxes.__path__, 'perg.syntaxes.'):
        yield importlib.import_module(name)


def print_match(
    filename,
    start_lineno,
    start_col,
    end_lineno,
    end_col,
    lines,
):
    prefix = f"{filename}:{start_lineno}: "
    for lineno in range(start_lineno, end_lineno+1):
        line = lines[lineno-1]
        if lineno == start_lineno:
            highlight_begin = start_col
        else:
            highlight_begin = 0
        if lineno == end_lineno:
            highlight_end = end_col
        else:
            highlight_end = len(line)

        before = line[:highlight_begin]
        match = line[highlight_begin:highlight_end]
        after = line[highlight_end:]

        red = '\u001b[31m'
        endred = '\u001b[0m'

        if lineno != start_lineno:
            prefix = " " * len(prefix)
        print(f"{prefix} {before}{red}{match}{endred}{after}")


def pattern_is_trivial(check_fn, pattern):
    """This tests a pattern against the empty string and each of the first 255 characters except newline. If all of
    them match, the pattern is considered trivial. Example patterns that would match this:
        .*
        .?
    """
    test_strings = [''] + [chr(c) for c in range(1, 255) if chr(c) != '\n']
    return all([check_fn(pattern, ts) for ts in test_strings])


def main():
    args = parse_args()

    syntaxes = list(find_syntaxes())
    for filename in find_files(args.paths):
        matches = set()

        for syntax in syntaxes:
            try:
                with open(filename) as f:
                    lines = [l.rstrip('\n') for l in f]
            except UnicodeDecodeError:
                continue

            with open(filename) as f:
                for (start_lineno, start_col, end_lineno, end_col, pattern, check_fns) in syntax.parse(f, filename):
                    for check_fn in check_fns:
                        if check_fn(pattern, args.text):
                            if not (args.ignore_trivial_match and pattern_is_trivial(check_fn, pattern)):
                                matches.add((filename, start_lineno, start_col, end_lineno, end_col))

        for match in sorted(matches):
            print_match(*match, lines)

if __name__ == "__main__":
    main()
