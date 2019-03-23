#!/usr/bin/env python3
"""Recursive descent parser in python"""

import re

class ParseIgnore():
    """Class to represent empty parse results so that we can
    still use None"""
    def __repr__(self):
        return "ParseIgnore"
PIgnore = ParseIgnore()

class Parsed():
    """Storage class for the result of parsing a string.
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
            return'Parsed(parsed="{}", left="{}", error={})'.format(
                self.parsed, self.left,self.error)
        return 'Parsed(parsed="{}", left="{}", result={})'.format(
                self.parsed, self.left,self.result)

    def posIn(self,string):
        """Work back the position in a base string based on what's left
        to parse"""
        if not string.endswith(self.left):
            raise ValueError("Wrong string for parsed object")
        consumed = string[:-len(self.left)]
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

class ParseRE(Parser):
    """ Parse a regex from the front of a string """
    ignore = False
    regex = re.compile('')
    expected = ''
    group = slice(None,None)
    def __init__(self, regex=None, ignore=False):
        self._regex = re.compile(regex) if regex else self.regex
        self.ignore = ignore

    def parse(self, string):
        Parser.PARSES +=1
        match = self._regex.match(string)
        result = PIgnore if self.ignore else None
        if match:
            parsed = match.group(0)[self.group]
            return Parsed(parsed, string[match.span()[1]:],"",result)
        return Parsed("",string,self.expected or "Expected match of /{}/"
                .format(self._regex.pattern))

class ParseStr(ParseRE):
    def __init__(self,string):
        self.expected = "Expected {}".format(string)
        self._regex = re.compile(re.escape(string))

"""
Parsers for combining other parsers in sequence
"""

class ParseObjectEither():
    """Object to store the successful result of the or'ing of parsers, if any,
    and which of the parsers succeeded"""
    def __init__(self,result,index):
        self.choice = result
        self.index = index
    def __repr__(self):
        return "Option({}: {})".format(self.index,self.choice)

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
    """Parser that tries 2 parsers and succeeds if both succeed.
    Ignore the whitespace between them."""
    def __init__(self, p1, p2):
        self._parsers = [spaces, p1, spaces, p2, spaces]

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
        self._parsers.append(spaces)
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
class String(ParseRE):
    regex = re.compile(r'"(\\"|[^"])*"')
    group = slice(1,-1)

class Int(ParseRE):
    regex = re.compile(r'-?[0-9]+')
    def parse(self, string):
        Parser.PARSES +=1
        result = super().parse(string)
        if result:
            result.result = int(result.result)
        return result

class Float(ParseRE):
    regex = re.compile(r'-?[0-9]*\.?[0-9]+')
    def parse(self, string):
        Parser.PARSES +=1
        result = super().parse(string)
        if result:
            result.result = float(result.result)
        return result

class Bool(ParseRE):
    regex = re.compile(r'(true|false)')

class Spaces(Parser):
    """Parse spaces and discard the result"""
    def parse(self, string):
        Parser.PARSES +=1
        p = ParseRE(r'\s*',ignore=True)
        return p.parse(string)

spaces = Spaces()

class SpacesAround(Parser):
    def __init__(self,other):
        self._other = other

    def parse(self, string):
        Parser.PARSES +=1
        p = Spaces() & self._other & Spaces()
        return p.parse(string)

class Delim(ParseRE):
    """Use a string as a delimiter, parsing it and any spaces around it"""
    def __init__(self,string):
        self.expected = "Expected {}".format(string)
        self._regex = re.compile(r'\s*{}\s*'.format(re.escape(string)))
        self.ignore = True

if __name__ == '__main__':
    print(String().parse('"5"'))
