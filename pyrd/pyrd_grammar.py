"""Hand-written recursive descent parser for the pyrd grammar"""
from .pyrd import *
from .pyrd_gen import *
import sys
import re

""" Parsers """

class Grammar(Parser):
    def parse(self,string):
        parsed = (Rules() & Delim("%%") 
                & PySuffix()).parse(string)
        if parsed:
            parsed.result = GrammarResult(parsed.result[0][::-1],
                                          parsed.result[1])
        return parsed

class PySuffix(ParseRE):
    regex = re.compile(r'(\n|[^\n])*')

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
            parsed.result = LexResult(parsed.result.results[0].index,
                                      parsed.result.results[0].choice)
        return parsed

class Regex(ParseRE):
    regex = re.compile(r"/(\\/|[^/])*/")
    group = slice(1,-1)

class Id(ParseRE):
    regex = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")

