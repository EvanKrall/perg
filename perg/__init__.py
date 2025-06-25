from dataclasses import dataclass
from functools import cached_property
from functools import total_ordering
from typing import Callable
from typing import Generic
from typing import Protocol
from typing import Tuple
from typing import IO
from typing import TypeVar
from typing import Optional

from perg.color import RED
from perg.color import RESET



@total_ordering
@dataclass(frozen=True)
class Location:
    filename: str
    start_lineno: int
    start_col: int
    end_lineno: int
    end_col: int

    def __lt__(self, other):
        assert isinstance(other, Location)
        return (
            self.filename,
            self.start_lineno,
            self.start_col,
            self.end_lineno,
            self.end_col,
        ) < (
            other.filename,
            other.start_lineno,
            other.start_col,
            other.end_lineno,
            other.end_col,
        )

    def print_highlighted(self, before=0, context=0, after=0):
        with open(self.filename) as f:
            lines = [l.rstrip('\n') for l in f]

        def prefix_unpadded(lineno):
            if lineno == self.start_lineno:
                return f"{self.filename}:{lineno}: "
            else:
                return f"{self.filename}-{lineno}- "

        longest_lineno = min(self.end_lineno + max(context, after), len(lines))
        longest_prefix = prefix_unpadded(longest_lineno)

        def prefix(lineno):
            return f"{prefix_unpadded(lineno):<{len(longest_prefix)}}"

        if before or context or after:
            print('---')

        if before or context:
            before_context_lines = max(before, context)
            start_context = max(1, self.start_lineno - before_context_lines)
            for lineno in range(start_context, self.start_lineno):
                print(f"{prefix(lineno)} {lines[lineno-1]}")

        for lineno in range(self.start_lineno, self.end_lineno+1):
            line = lines[lineno-1]
            if lineno == self.start_lineno:
                highlight_begin = self.start_col
            else:
                highlight_begin = 0
            if lineno == self.end_lineno:
                highlight_end = self.end_col
            else:
                highlight_end = len(line)

            before = line[:highlight_begin]
            match = line[highlight_begin:highlight_end]
            after_text = line[highlight_end:]
            print(f"{prefix(lineno)} {before}{RED}{match}{RESET}{after_text}")

        if after or context:
            after_context_lines = max(after, context)
            end_context = min(len(lines), self.end_lineno + after_context_lines)
            for lineno in range(self.end_lineno+1, end_context):
                line = lines[lineno-1]
                print(f"{prefix(lineno)} {line}")

@dataclass(frozen=True)
class CheckResult:
    text: str
    spans: Tuple[Tuple[int, int], ...]  # the spans (start, end) of text which matched.


T = TypeVar('T')
CheckFunction = Callable[[T, str, int], Optional[CheckResult]]


@total_ordering
@dataclass(frozen=True)
class Pattern(Generic[T]):
    location: Location
    value: T
    check_fns: Tuple[CheckFunction[T], ...]

    def __lt__(self, other):
        assert isinstance(other, Pattern)
        return (
            self.location,
            self.value,
        ) < (
            other.location,
            other.value,
        )


class NoMatchError(Exception):
    pass


@total_ordering
@dataclass(frozen=True)
class Match(Generic[T]):
    check_fn: CheckFunction[T]
    pattern: Pattern[T]
    text: str
    partial: bool

    def __post_init__(self):
        self.result

    @cached_property
    def result(self):
        result = self.check_fn(self.pattern.value, self.text, self.partial)
        if not result:
            raise NoMatchError()
        return result

    def __lt__(self, other):
        assert isinstance(other, Match)
        return (
            self.pattern,
            self.text,
            self.partial,
        ) < (
            other.pattern,
            other.text,
            other.partial,
        )


DEBUG = False

def debug(s):
    if DEBUG:
        print(s)


class Syntax(Protocol):
    def parse(self, f: IO, filename: str):
        ...
