from pyrd import *
import sys
import re

class Program(Parser):
    def parse(self, string):
        parsed = (Prefix() & Grammar() & Suffix()).parse(string)
class Grammar(Parser):
    def parse(self,string):
        parsed = (Delim("%%") & Rules() & Delim("%%")).parse(string)
        return parsed

class Rules(Parser):
    def parse(self,string):
        parsed = ( Rule() & Delim(";") & Rules()
                 | Rule() & Delim(";")).parse(string)
        return parsed

class Rule(Parser):
    def parse(self, string):
        parsed = (Id() & Delim("::") & Sequences()).parse(string)
        return parsed

class Sequences(Parser):
    def parse(self, string):
        parsed = (Sequence() & Delim('|') & Sequences() 
                 | Sequence()).parse(string)
        return parsed

class Sequence(Parser):
    def parse(self, string):
        parsed = (Lexers() & Function()
                 | Lexers()).parse(string)
        return parsed

class Function(Parser):
    def parse(self, string):
        parsed = (Delim('{') & PyLit() & Delim('}')).parse(string)
        return parsed

class PyLit(ParseRE):
    REGEX = re.compile(r'[^{}]*')

class Lexers(Parser):
    def parse(self,string):
        parsed = (Lexer() & Lexers() | Lexer()).parse(string)
        return parsed

class Lexer(Parser):
    def parse(self,string):
        parsed = SpacesAround(Id() | String() | Regex()).parse(string)
        return parsed

class Regex(ParseRE):
    REGEX = re.compile(r"/([^/]*)/")

class Id(ParseRE):
    REGEX = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

if __name__=='__main__':
    with open(sys.argv[1]) as gramf:
        to_parse = gramf.read()
        parsed = Grammar().parse(to_parse)
        if parsed:
            print(parsed.result)
        else:
            print(parsed.err(to_parse))
