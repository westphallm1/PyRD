#!/usr/bin/env python3
"""Recursive descent parser in python"""

import re

DIGITS="0123456789"
LETTERS="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

class ParseIgnore():
    """Class to represent empty parse results so that we can
    still use None"""
    def __repr__(self):
        return "ParseIgnore"
PIgnore = ParseIgnore()

class Parsed():
    """Storage object for the result of parsing a string.
    Contains: the parsed characters, the unparsed characters,
    and an error message"""
    def __init__(self,parsed="",left="",error="",result=None):
        self.parsed = parsed
        self.left = left
        self.error = error
        # default behavior: result is the parsed string
        self.result = result or parsed

    def __bool__(self):
        """Parsed is truthy if there's no error, false otherwise"""
        return not self.error

    def __repr__(self):
        if self.error:
            return'Parsed(parsed="{}", left="{}", error="{}")'.format(
                self.parsed, self.left,self.error)
        return 'Parsed(parsed="{}", left="{}", result={})'.format(
                self.parsed, self.left,self.result)

    def posIn(self,string):
        """Work back the position in a base string based on what's left
        to parse"""
        if not string.endswith(self.left):
            raise ValueError("Wrong string for parsed object")
        consumed = string[:len(self.left)]
        line = consumed.count('\n')+1
        char = len(consumed) - max(consumed.rfind('\n'),0)
        return line, char

    def err(self,string):
        line, char = self.posIn(string)
        return "Line {}: {}".format(line,self.error)


class Parser():
    PARSES = 0
    def parse(self, string):
        Parser.PARSES +=1
        """Default behavior: parse no characters successfully"""
        return Parsed(parsed="", left=string, error="")

    def __or__(self,other):
        """ Make a ParseOr """
        return ParseOr(self,other)

    def __and__(self,other):
        """ Make a ParseAnd """
        return ParseAnd(self,other)

class ParseOne(Parser):
    """Parse a single character off the front of the string"""
    def parse(self, string):
        Parser.PARSES +=1
        if len(string) == 0:
            return Parsed("","","EOF")
        return Parsed(string[0],string[1:],"")

class ParseA(Parser):
    """ Parse a set of characters """
    def __init__(self,chars):
        self._chars = chars

    def parse(self, string):
        Parser.PARSES +=1
        if string.startswith(self._chars):
            return Parsed(self._chars,string[len(self._chars):],"")
        else:
            return Parsed("",string,"Expected {}".format(self._chars))

class ParseAny(ParseA):
    """ Parse one of several sets of characters """
    def parse(self, string):
        Parser.PARSES +=1
        for chars in self._chars:
            if string.startswith(chars):
                return Parsed(chars,string[len(chars):],"")
        return Parsed("",string,"Expected one of {}".format(self._chars))

class ParseRE(Parser):
    """ Parse a regex from the front of a string """
    def __init__(self,regex):
        self._regex = re.compile(regex)

    def parse(self, string):
        Parser.PARSES +=1
        match = self._regex.match(string)
        if match:
            return Parsed(match.group(bool(match.groups())),
                          string[match.span()[1]:],"")
        return Parsed("",string,"Expected match of /{}/"
                .format(self._regex.pattern))



"""
Parsers for combining other parsers in sequence
"""

class ParseObjectEither():
    """Object to store the successful result of the or'ing of parsers, if any,
    and which of the parsers succeeded"""
    def __init__(self,parsed,index):
        self.result = parsed
        self.index = index
    def __repr__(self):
        return "Option({}: {})".format(self.index,self.result)

class ParseOr(Parser):
    """Parser that tries 2 parsers and succeeds if either succeeds"""
    def __init__(self, p1, p2):
        self._parsers = [p1, p2]

    def parse(self, string):
        Parser.PARSES +=1
        for i,parser in enumerate(self._parsers):
            parsed = parser.parse(string)
            if parsed:
                parsed.result = ParseObjectEither(parsed.result,i)
                return parsed
        return parsed

    def __or__(self,other):
        self._parsers.append(other)
        return self

class ParseObjectBoth():
    """Object to store the results of multiple parsers concatenated with '&'
    """
    def __init__(self):
        self.results = []

    def append(self,result):
        if result is not PIgnore:
            self.results.append(result)

    def __repr__(self):
        return self.results.__repr__()
    
    def __getitem__(self,*args,**kwargs):
        return self.results.__getitem__(*args,**kwargs)

class ParseAnd(Parser):
    """Parser that tries 2 parsers and succeeds if both succeed"""
    def __init__(self, p1, p2):
        self._parsers = [p1, p2]

    def parse(self, string):
        Parser.PARSES +=1
        parsed_strings = []
        results = ParseObjectBoth()
        for parser in self._parsers:
            parsed = parser.parse(string)
            if not parsed:
                return parsed
            parsed_strings.append(parsed.parsed)
            results.append(parsed.result)
            string = parsed.left

        return Parsed(''.join(parsed_strings),string,"",results)

    def __and__(self,other):
        self._parsers.append(other)
        return self



""" Meta-parsers that take another parser as input """

class Ignore(Parser):
    """Perform the action of another parser, discarding its result but keeping
    errors"""
    def __init__(self,other):
        self._other = other

    def parse(self, string):
        Parser.PARSES +=1
        result = self._other.parse(string)
        result.result = PIgnore
        return result

"""Common utility parsers"""
class ParseString(ParseRE):
    STRING_RE = re.compile(r'"([^"]*)"')
    def __init__(self):
        self._regex = self.STRING_RE

class ParseInt(ParseRE):
    INT_RE = re.compile(r'-?[0-9]+')
    def __init__(self):
        self._regex = self.INT_RE
    def parse(self, string):
        Parser.PARSES +=1
        result = super().parse(string)
        if result:
            result.result = int(result.result)
        return result

class ParseFloat(ParseRE):
    FLOAT_RE = re.compile(r'-?[0-9]*\.?[0-9]+')
    def __init__(self):
        self._regex = self.FLOAT_RE
    def parse(self, string):
        Parser.PARSES +=1
        result = super().parse(string)
        if result:
            result.result = float(result.result)
        return result

class ParseBool(ParseRE):
    BOOL_RE = re.compile(r'(true|false)')
    def __init__(self):
        self._regex = BOOL_RE

class Spaces(Parser):
    def parse(self, string):
        Parser.PARSES +=1
        p = Ignore(ParseRE(r'[ \t\n]*'))
        return p.parse(string)

class SpacesAround(Parser):
    def __init__(self,other):
        self._other = other

    def parse(self, string):
        Parser.PARSES +=1
        p = Spaces() & self._other & Spaces()
        return p.parse(string)

if __name__ == '__main__':
    p = ParseA('[') & ParseInt() & ParseA(']')
    print(p,p._parsers,p.parse("[5]"))
