import sys
import re
import syntaxes

class Perg(object):
	def __init__(self, *args):
		#TODO optparse
		self.text = args[0]
		self.paths = args[1:]

	def findFiles(self):
		"""Find all the filenames described by self.paths, open them, and yield them and the syntax associated with them"""
		#TODO recursive (-r)
		if not self.paths:
			yield ('<stdin>', sys.stdin, 'general')
		else:
			for path in self.paths:
				yield (path, open(path, 'r'), 'general')

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
