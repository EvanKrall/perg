import sys
import re


class Perg(object):
	def __init__(self, text, *paths):
		#TODO optparse
		self.text = text
		self.paths = paths

	def findFiles(self):
		"""Find all the filenames described by self.paths, open them, and yield them and the syntax associated with them"""
		#TODO recursive (-r)
		if not self.paths:
			yield ('<stdin>', sys.stdin, 'general')
		else:
			for path in self.paths:
				if path.endswith('.py'):
					syntax = 'python2'
				else:
					syntax = 'general'
				yield (path, open(path, 'r'), syntax)

	def getRegexes(self, f, syntax_name):
		"""Given a file object and a syntax name, attempt to yield all the regexes."""
		parser = getattr(__import__('perg.syntaxes.%s' % syntax_name).perg.syntaxes, syntax_name)
		return parser.parse(f)


	def checkMatch(self, regex):
		"""Given a regex, see if it matches our string."""
		#TODO options for matching only the beginning.
		return re.search(regex, self.text)


	def printMatch(self, filename, lineno, column, literal):
		print "%s:%d:%d:%s" % (filename, lineno, column, literal)

	def run(self):
		for (filename, f, syntax) in self.findFiles():
			for (lineno, column, regex, literal) in self.getRegexes(f, syntax):
				if self.checkMatch(regex):
					self.printMatch(filename, lineno, column, literal)


if __name__ == "__main__":
	Perg(*sys.argv[1:]).run()
