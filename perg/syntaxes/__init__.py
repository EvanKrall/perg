from enum import Enum


class Relevance(Enum):
	NO = 0
	MAYBE = 1
	YES = 2


class PergSyntaxParseError(Exception):
	pass
