import sys


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
                    syntax = 'python'
                else:
                    syntax = 'general'
                yield (path, open(path, 'r'), syntax)

    def getRegexes(self, f, syntax_name):
        """Given a file object and a syntax name, attempt to yield all the regexes."""
        parser = getattr(__import__('perg.syntaxes.%s' % syntax_name).syntaxes, syntax_name)
        return parser.parse(f)

    def run(self):
        for (filename, f, syntax) in self.findFiles():
            for (lineno, column, regex, literal, check_fns) in self.getRegexes(f, syntax):
                for check_fn in check_fns:
                    if check_fn(regex, self.text):
                        print(f"{filename}:{lineno}:{column}:{literal}")


if __name__ == "__main__":
    Perg(*sys.argv[1:]).run()
