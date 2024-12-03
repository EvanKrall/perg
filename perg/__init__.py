from dataclasses import dataclass
from functools import total_ordering
from typing import Callable
from typing import Tuple

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


@dataclass(frozen=True)
class Pattern:
	location: Location
	value: str
	check_fns: Tuple[Callable, ...]


@dataclass(frozen=True)
class CheckResult:
	text: str
	span: Tuple[int, int]  # the span (start, end) of text which matched.


@dataclass(frozen=True)
class Match:
	check_fn: Callable
	pattern: Pattern
	result: CheckResult