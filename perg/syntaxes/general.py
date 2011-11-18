# A general-purpose string literal finder for perg.

def parse(f):
	for lineno, line in enumerate(f.readlines()):
		yield lineno, 0, line.rstrip('\n'), line.rstrip('\n')