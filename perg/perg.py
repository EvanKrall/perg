import argparse
import os.path
import os
import pkgutil
import importlib
from collections import defaultdict

import perg.syntaxes
from perg import heuristics

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
    parser.add_argument(
        '--min-undeletable',
        type=int,
        default=0,
        help="If enabled, this heuristic will check the pattern against versions of your string with single characters"
             " deleted. If too many characters are deletable with the pattern still matching, the pattern is ignored."
    )
    parser.add_argument(
        '--max-deletable',
        type=int,
        default=-1,
        help="If enabled, this heuristic will check the pattern against versions of your string with single characters"
             " deleted. If too many characters are deletable with the pattern still matching, the pattern is ignored."
    )
    parser.add_argument(
        '--print-checker-names',
        action=argparse.BooleanOptionalAction,
        help="Print the names of all the checkers that matched the pattern to the string after each match.",
        default=False,
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
    checker_names,
    lines,
    args,
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
        reset = '\u001b[0m'

        if lineno != start_lineno:
            prefix = " " * len(prefix)
        print(f"{prefix} {before}{red}{match}{reset}{after}")

    if args.print_checker_names:
        boldblack = '\u001b[30;1m'
        print(f"{boldblack}({', '.join(checker_names)}){reset}\n")

def passes_heuristics(check_fn, pattern, s, args):
    if args.ignore_trivial_match and heuristics.pattern_is_trivial(check_fn, pattern):
        return False

    if args.max_deletable != -1 or args.min_undeletable > 0:
        if heuristics.too_many_things_deletable(
            check_fn,
            pattern,
            s,
            max_deletable=args.max_deletable,
            min_undeletable=args.min_undeletable,
        ):
            return False

    return True


def main():
    args = parse_args()

    syntaxes = list(find_syntaxes())
    for filename in find_files(args.paths):
        matches = defaultdict(set)

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
                            if passes_heuristics(check_fn, pattern, args.text, args):
                                matches[(filename, start_lineno, start_col, end_lineno, end_col)].add(check_fn.__name__)

        for match, checkers in sorted(matches.items()):
            print_match(*match, checkers, lines, args)

if __name__ == "__main__":
    main()
