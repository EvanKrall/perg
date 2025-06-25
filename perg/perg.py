import argparse
import functools
import importlib
import os.path
import os
import pdb
import pkgutil
import sys
import traceback
import warnings

from collections import defaultdict
from typing import Collection
from typing import List
from typing import Iterator
from typing import Tuple

import perg.syntaxes
from perg.syntaxes import Relevance
from perg.syntaxes import PergSyntaxParseError
from perg import heuristics
from perg import Match
from perg import CheckResult
from perg import Location
from perg import debug
from perg import Syntax
from perg import NoMatchError
from perg.color import BRIGHT_YELLOW
from perg.color import RESET
from perg.color import BRIGHT
from perg.color import GREEN
from perg.color import CYAN
from perg.color import BLUE
from perg.color import BRIGHT_PURPLE
import perg


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
        action=argparse.BooleanOptionalAction,
        help="Show patterns that only match a portion of your string.",
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
    parser.add_argument(
        '--no-heuristics',
        action='store_true',
        default=False,
    )
    parser.add_argument(
        '--debug',
        action=argparse.BooleanOptionalAction,
        help="Print debug messages.",
        default=False,
    )
    parser.add_argument(
        '--score-by-information',
        action=argparse.BooleanOptionalAction,
        help="Score matches by the amount of information they give.",
        default=True,
    )
    parser.add_argument(
        '--show-score',
        action=argparse.BooleanOptionalAction,
        help="Show how much of the information in the string is implied by the pattern.",
        default=False,
    )
    parser.add_argument(
        '--pct-of-best-score',
        type=float,
        default=50.0,
        help="Only show matches with a score that's at least this percent of the best-scoring match.",
    )

    args = parser.parse_args()
    # if args.show_highlighted_partial_match is None:
    #     args.show_highlighted_partial_match = args.partial

    if args.debug:
        perg.DEBUG = True
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
    location: Location,
    scored_matches: Collection[Tuple[float, Match]],
    args,
):

    location.print_highlighted(args.before, args.context, args.after)

    matches_by_score_and_result: dict[Tuple[float, CheckResult], List[Match]] = {}
    for score, match in scored_matches:
        matches_by_score_and_result.setdefault((score, match.result), []).append(match)

    for (score, result), matches2 in matches_by_score_and_result.items():
        text = result.text
        checker_names = [match.check_fn.__name__ for match in matches2]
        if args.print_checker_names:
            print(f"{BRIGHT_PURPLE}({', '.join(checker_names)}):{RESET} ", end='')

        colors = [RESET for _ in text]

        lastend=0
        for span in result.spans:
            start, end = span
            for i in range(start, end):
                colors[i] = BRIGHT

        replaceable = heuristics.replaceable_chars(match)
        deletable = heuristics.deletable_chars(match)
        for i in deletable:
            colors[i] = GREEN

        for i in replaceable:
            if i in deletable:
                colors[i] = CYAN
            else:
                colors[i] = BLUE

        if args.show_highlighted_partial_match:
            print(''.join(color+char+RESET for color, char in zip(colors, text)))
        if args.show_score:
            print(f"{BRIGHT_YELLOW}Score: {score}{RESET}")

    print()


def passes_heuristics_first_pass(match, args):
    if args.no_heuristics:
        return True

    if args.ignore_empty_match and heuristics.pattern_matches_empty(match):
        return False

    if args.ignore_single_char_match and heuristics.pattern_matches_single_char(match):
        return False

    if args.max_deletable != -1 or args.min_undeletable > 0:
        if heuristics.too_many_things_deletable(
            match.check_fn,
            match.pattern,
            match.text,
            partial=args.partial,
            max_deletable=args.max_deletable,
            min_undeletable=args.min_undeletable,
        ):
            return False

    return True


def run_syntax_on_file(syntax: Syntax, filename: str, text: str, partial: bool) -> Iterator[Match]:
    debug(f"trying {syntax} on {filename}")
    with open(filename) as f:
        for pattern in syntax.parse(f, filename):
            debug(pattern)
            for check_fn in pattern.check_fns:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    try:
                        yield Match(check_fn, pattern, text, partial)
                    except NoMatchError:
                        pass

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
    matches = set()

    for filename in find_files(args.paths):
        syntax_relevances = group_syntaxes_by_relevance(all_syntaxes, filename)
        debug(syntax_relevances)

        successful_parse = False
        for relevance in [Relevance.YES, Relevance.MAYBE]:
            if syntaxes := syntax_relevances[relevance]:
                for syntax in syntaxes:
                    try:
                        for match in run_syntax_on_file(syntax, filename, args.text, args.partial):
                            if passes_heuristics_first_pass(match, args):
                                matches.add(match)
                        successful_parse = True
                    except PergSyntaxParseError:
                        if relevance == Relevance.YES:
                            # if we think the syntax is definitely relevant, we should raise an error if we can't parse.
                            raise
                        else:
                            pass
                    except Exception as e:
                        if args.print_errors:
                            print(f"syntax {syntax} errored on {filename}:")
                            traceback.print_exc()
                        if args.debug_errors:
                            extype, value, tb = sys.exc_info()
                            traceback.print_exc()
                            pdb.post_mortem(tb)
                        if args.raise_errors:
                            raise
                break  # if we have any YES syntaxes, don't run the MAYBEs.
        if not successful_parse:
            debug(
                f"Couldn't parse file {filename} with syntax{'es' if len(syntaxes) > 1 else ''} {', '.join(s.__name__ for s in syntaxes)}",
            )

    if args.score_by_information:
        match_score_fn = heuristics.information
    else:
        match_score_fn = lambda x: 1

    scored_matches = sorted(
        ((match_score_fn(match), match) for match in matches),
        reverse=True,
    )
    if scored_matches:
        best_score, _ = scored_matches[0]
        threshold = args.pct_of_best_score * best_score / 100
        for i, (score, match) in enumerate(scored_matches):
            if score < threshold:
                scored_matches = scored_matches[:i]
                break

    scored_matches_by_location: Dict[Location, List[Tuple[float, Match]]] = {}
    for score, match in scored_matches:
        scored_matches_by_location.setdefault(match.pattern.location, []).append((score, match))

    for location, scored_matches_for_location in scored_matches_by_location.items():
        print_match(location, scored_matches_for_location, args)

if __name__ == "__main__":
    main()
