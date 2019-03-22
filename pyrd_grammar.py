from pyrd import *
import sys
import re

""" Storage classes for the results of parsing various types """
class LexResult():
    def __init__(self,result):
        self.index = result.index
        self.choice = result.choice

    def __repr__(self):
        format_ = ["Id({})",'String("{}")',"Regex(/{}/)"][self.index]
        return format_.format(self.choice)

class SeqResult():
    def __init__(self,lexers,function):
        self.lexers = lexers
        self.function = function

    def __repr__(self):
        lexers = '\n'.join('      {}'.format(l) for l in self.lexers)
        return "Sequence(function={{{}}},lexers=\n{})".format(
                    self.function,lexers)

class RuleResult():
    def __init__(self,id_,sequences):
        self.id = id_
        self.sequences = sequences

    def __repr__(self):
        seqs = '\n'.join('    {}'.format(s) for s in self.sequences)
        return "Rule(id={},sequences=\n{})".format(self.id,seqs)

class GrammarResult():
    def __init__(self,rules):
        self.rules = rules

    def __repr__(self):
        rules = '\n'.join('  {}'.format(r) for r in self.rules)
        return "Grammar(rules=\n{})".format(rules)

""" Parsers """
class Program(Parser):
    def parse(self, string):
        parsed = (Prefix() & Grammar() & Suffix()).parse(string)

class Grammar(Parser):
    def parse(self,string):
        parsed = (Delim("%%") & Rules() & Delim("%%")).parse(string)
        if parsed:
            parsed.result = GrammarResult(parsed.result[0][::-1])
        return parsed

class Rules(Parser):
    def parse(self,string):
        parsed = ( Rule() & Delim(";") & Rules()
                 | Rule() & Delim(";")).parse(string)
        if parsed:
            if parsed.result.index == 0:
                rule, rules = parsed.result.choice
                rules.append(rule)
                parsed.result = rules
            else:
                parsed.result = [parsed.result.choice[0]]
        return parsed

class Rule(Parser):
    def parse(self, string):
        parsed = (Id() & Delim("::") & Sequences()).parse(string)
        if parsed:
            parsed.result = RuleResult(parsed.result[0],parsed.result[1][::-1])
        return parsed

class Sequences(Parser):
    def parse(self, string):
        parsed = (Sequence() & Delim('|') & Sequences() 
                 | Sequence()).parse(string)
        if parsed:
            if parsed.result.index == 0:
                sequence, sequences = parsed.result.choice
                sequences.append(sequence)
                parsed.result = sequences
            else:
                parsed.result = [parsed.result.choice]

        return parsed

class Sequence(Parser):
    def parse(self, string):
        parsed = (Lexers() & Function()
                 | Lexers()).parse(string)
        if parsed:
            if parsed.result.index == 0:
                lexers, function = parsed.result.choice
                lexers = lexers[::-1]
            else:
                lexers = parsed.result.choice[::-1]
                function = None
            parsed.result = SeqResult(lexers,function)
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
    """Support bracket characters inside python-literal expressions"""
    def parse(self, string):
        parsed = (Delim('{') & PyLit() & Delim('}')).parse(string)
        if parsed:
            parsed.result = '{{{}}}'.format(parsed.result[0])
        return parsed

class Lexers(Parser):
    def parse(self,string):
        parsed = (Lexer() & Lexers() | Lexer()).parse(string)
        if parsed:
            if parsed.result.index == 0:
                lexer,lexers  = parsed.result.choice
                lexers.append(lexer)
                parsed.result = lexers
            else:
                parsed.result = [parsed.result.choice]
        return parsed

class Lexer(Parser):
    def parse(self,string):
        parsed = SpacesAround(Id() | String() | Regex()).parse(string)
        if parsed:
            parsed.result = LexResult(parsed.result.results[0])
        return parsed

class Regex(ParseRE):
    regex = re.compile(r"/([^/]*)/")

class Id(ParseRE):
    regex = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

if __name__=='__main__':
    with open(sys.argv[1]) as gramf:
        to_parse = gramf.read()
        parsed = Grammar().parse(to_parse)
        if parsed:
            print(parsed.result)
        else:
            print(parsed.err(to_parse))
