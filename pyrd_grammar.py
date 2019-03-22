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
        if parsed:
            parsed.result = parsed.result[0]
        return parsed

class PyLit(Parser):
    def parse(self, string):
        parsed = (PyStr() & PyBrack() & PyLit()
                  | PyStr()).parse(string)
        if parsed:
            if parsed.result.index == 0:
                parsed.result = ''.join(parsed.result.choice.results)
            else:
                parsed.result = parsed.result.choice
        return parsed


class PyStr(ParseRE):
    regex = re.compile(r'[^{}]*')

class PyBrack(Parser):
    def parse(self, string):
        parsed = (Delim('{') & PyLit() & Delim('}')).parse(string)
        if parsed:
            parsed.result = '{{{}}}'.format(parsed.result[0])
        return parsed

class Lexers(Parser):
    def parse(self,string):
        parsed = (Lexer() & Lexers() | Lexer()).parse(string)
        return parsed

class Lexer(Parser):
    def parse(self,string):
        parsed = SpacesAround(Id() | String() | Regex()).parse(string)
        return parsed

class Regex(ParseRE):
    regex = re.compile(r"/([^/]*)/")

class Id(ParseRE):
    regex = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

if __name__=='__main__':
    print(Function().parse("{return {'foo':5}}"))
    print(Function().parse("{return [5,6,7]}"))
    print(Function().parse("{return {'foo':{'bar':'baz'}}}"))
    exit(0)
    with open(sys.argv[1]) as gramf:
        to_parse = gramf.read()
        parsed = Grammar().parse(to_parse)
        if parsed:
            print(parsed.result)
        else:
            print(parsed.err(to_parse))
