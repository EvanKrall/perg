import argparse
import importlib
import os.path
import os
import pdb
import pkgutil
import sys
import traceback
import warnings

from collections import defaultdict

import perg.syntaxes
from perg.syntaxes import Relevance
from perg import heuristics
from perg import Match

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
        '--ignore-empty-match',
        action=argparse.BooleanOptionalAction,
        help="Ignore patterns that match the empty string.",
        default=True,
    )
    parser.add_argument(
        '--ignore-single-char-match',
        action=argparse.BooleanOptionalAction,
        help="Ignore patterns that match all single-character strings",
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
    parser.add_argument(
        '--partial',
        nargs='?',
        const=1,
        type=int,
        default=-1,
        help=(
            'Show patterns that match a substring of at least length N of your text.'
            ' (if --partial is not specified, patterns must match the whole text.)'
            ' --partial by itself requires a match of at least 1 character.'
            ' --partial=N allows you to specify a minimum length.'
        )
    )

    parser.add_argument(
        '-A', '--after',
        type=int,
        default=0,
    )
    parser.add_argument(
        '-B', '--before',
        type=int,
        default=0,
    )
    parser.add_argument(
        '-C', '--context',
        type=int,
        default=0,
    )
    parser.add_argument(
        '--print-errors',
        action=argparse.BooleanOptionalAction,
        help="Print tracebacks for errors when running syntaxes on files.",
        default=False,
    )
    parser.add_argument(
        '--raise-errors',
        action=argparse.BooleanOptionalAction,
        help="Don't catch exceptions when running syntaxes on files.",
        default=True,
    )
    parser.add_argument(
        '--debug-errors', '--pdb',
        action=argparse.BooleanOptionalAction,
        help="Use PDB to post-mortem debug when errors occur.",
        default=False,
    )
    parser.add_argument(
        '--syntax-allowlist',
        type=str,
        nargs='+',
        default=(),
    )
    parser.add_argument(
        '--show-highlighted-partial-match',
        action=argparse.BooleanOptionalAction,
        help="Show your original string with the partial match highlighted. Defaults to on with --partial.",
        default=None,
    )


    args = parser.parse_args()
    if args.show_highlighted_partial_match is None:
        args.show_highlighted_partial_match = (args.partial >= 0)
    return args


def find_syntaxes(syntax_allowlist=()):
    syntaxes = []
    found_syntax_names = set()
    syntax_allowlist = set(syntax_allowlist)
    for _, name, _ in pkgutil.iter_modules(perg.syntaxes.__path__, 'perg.syntaxes.'):
        shortname = name.removeprefix('perg.syntaxes.')
        found_syntax_names.add(shortname)
        if shortname in syntax_allowlist or not syntax_allowlist:
            syntaxes.append(importlib.import_module(name))

    if syntax_allowlist:
        unfound_syntaxes = syntax_allowlist - found_syntax_names
        if unfound_syntaxes:
            raise ValueError(f"Couldn't find syntaxes from --syntax-allowlist: {unfound_syntaxes}. Found syntaxes: {found_syntax_names}")
    return syntaxes

def print_match(
    location,
    matches,
    lines,
    args,
):
    RESET = '\u001b[0m'
    RED = '\u001b[31;1m'
    YELLOW = '\u001b[33;1m'
    GREEN = '\u001b[32;1m'
    CYAN = '\u001b[36;1m'
    BLUE = '\u001b[34;1m'
    PURPLE = '\u001b[35;1m'
    BRIGHT = '\u001b[37;1m'

    def prefix_unpadded(lineno):
        if lineno == location.start_lineno:
            return f"{location.filename}:{lineno}: "
        else:
            return f"{location.filename}-{lineno}- "

    longest_lineno = min(location.end_lineno + max(args.context, args.after), len(lines))
    longest_prefix = prefix_unpadded(longest_lineno)

    def prefix(lineno):
        return f"{prefix_unpadded(lineno):<{len(longest_prefix)}}"

    if args.before or args.context or args.after:
        print('---')

    if args.before or args.context:
        before_context_lines = max(args.before, args.context)
        start_context = max(1, location.start_lineno - before_context_lines)
        for lineno in range(start_context, location.start_lineno):
            print(f"{prefix(lineno)} {lines[lineno-1]}")

    for lineno in range(location.start_lineno, location.end_lineno+1):
        line = lines[lineno-1]
        if lineno == location.start_lineno:
            highlight_begin = location.start_col
        else:
            highlight_begin = 0
        if lineno == location.end_lineno:
            highlight_end = location.end_col
        else:
            highlight_end = len(line)

        before = line[:highlight_begin]
        match = line[highlight_begin:highlight_end]
        after = line[highlight_end:]
        print(f"{prefix(lineno)} {before}{RED}{match}{RESET}{after}")

    if args.after or args.context:
        after_context_lines = max(args.after, args.context)
        end_context = min(len(lines), location.end_lineno + after_context_lines)
        for lineno in range(location.end_lineno+1, end_context):
            line = lines[lineno-1]
            print(f"{prefix(lineno)} {line}")

    if args.print_checker_names and not args.show_highlighted_partial_match:
        checker_names = [match.check_fn.__name__ for match in matches]
        print(f"{GREEN}({', '.join(checker_names)}){RESET}\n")

    if args.show_highlighted_partial_match:
        matches_by_result = {}
        for match in matches:
            matches_by_result.setdefault(match.result, []).append(match)

        for result, matches2 in matches_by_result.items():
            text = result.text
            start, end = result.span
            checker_names = [match.check_fn.__name__ for match in matches2]
            print(f"{GREEN}({', '.join(checker_names)}){RESET}: {text[:start]}{PURPLE}{text[start:end]}{RESET}{text[end:]}")


def passes_heuristics(check_fn, pattern, s, args):
    if args.ignore_empty_match and heuristics.pattern_matches_empty(check_fn, pattern):
        return False

    if args.ignore_single_char_match and heuristics.pattern_matches_single_char(check_fn, pattern):
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


def run_syntax_on_file(syntax, filename, matches, args):
    print(f"trying {syntax} on {filename}")
    with open(filename) as f:
        for pattern in syntax.parse(f, filename):
            for check_fn in pattern.check_fns:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    if check_result := check_fn(pattern.value, args.text, partial=args.partial):
                        if passes_heuristics(check_fn, pattern.value, args.text, args):
                            matches[pattern.location].add(Match(check_fn=check_fn, pattern=pattern, result=check_result))

def group_syntaxes_by_relevance(all_syntaxes, filename):
    syntax_scores = {
        Relevance.NO: [],
        Relevance.MAYBE: [],
        Relevance.YES: [],
    }

    for syntax in all_syntaxes:
        syntax_scores[syntax.check_relevance(filename)].append(syntax)

    return syntax_scores


def main():
    args = parse_args()

    all_syntaxes = list(find_syntaxes(args.syntax_allowlist))
    for filename in find_files(args.paths):
        syntax_relevances = group_syntaxes_by_relevance(all_syntaxes, filename)
        print(syntax_relevances)
        matches = defaultdict(set)

        try:
            with open(filename) as f:
                lines = [l.rstrip('\n') for l in f]
        except UnicodeDecodeError:
            continue

        successful_parse = False
        for relevance in [Relevance.YES, Relevance.MAYBE]:
            if syntaxes := syntax_relevances[relevance]:
                for syntax in syntaxes:
                    try:
                        run_syntax_on_file(syntax, filename, matches, args)
                        successful_parse = True
                    except Exception as e:
                        if args.print_errors:
                            print(f"syntax {syntax} errored on {filename}:")
                            traceback.print_exc()
                        elif args.debug_errors:
                            extype, value, tb = sys.exc_info()
                            traceback.print_exc()
                            pdb.post_mortem(tb)
                        elif args.raise_errors:
                            raise
                break  # if we have any YES syntaxes, don't run the MAYBEs.
        if not successful_parse:
            print(
                f"Couldn't parse file {filename} with syntax{'es' if len(syntaxes) > 1 else ''} {', '.join(syntaxes)}",
                file=sys.stderr,
            )

        for location, matches in sorted(matches.items()):
            print_match(location, matches, lines, args)

if __name__ == "__main__":
    main()
