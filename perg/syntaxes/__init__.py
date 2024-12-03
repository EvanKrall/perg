from enum import Enum

from typing import Callable
from typing import Tuple

class Relevance(Enum):
	NO = 0
	MAYBE = 1
	YES = 2


class PergSyntaxParseError(Exception):
	pass
