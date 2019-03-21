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

    def __repr__(self):
        if self.error:
            return self.error
        return 'Parsed(parsed="{}", left="{}", result={})'.format(
                self.parsed, self.left,self.result)

class Parser():
    def parse(self, string):
        """Default behavior: parse no characters successfully"""
        return Parsed(parsed="", left=string, error="")

    def __call__(self,*args,**kwargs):
        return self.parse(*args,**kwargs)

    def __or__(self,other):
        """ Make a ParseOr """
        return ParseOr(self,other)

    def __and__(self,other):
        """ Make a ParseAnd """
        return ParseAnd(self,other)

class ParseOne(Parser):
    """Parse a single character off the front of the string"""
    def parse(self,string):
        if len(string) == 0:
            return Parsed("","","EOF")
        return Parsed(string[0],string[1:],"")

class ParseA(Parser):
    """ Parse a set of characters """
    def __init__(self,chars):
        self._chars = chars

    def parse(self,string):
        if string.startswith(self._chars):
            return Parsed(self._chars,string[len(self._chars):],"")
        else:
            return Parsed("",string,"Expected {}".format(self._chars))

class ParseAny(ParseA):
    """ Parse one of several sets of characters """
    def parse(self,string):
        for chars in self._chars:
            if string.startswith(chars):
                return Parsed(chars,string[len(chars):],"")
        return Parsed("",string,"Expected one of {}".format(self._chars))

class ParseNot(ParseA):
    def parse(self,string):
        if string.startswith(self._chars):
            return Parsed("",string,"Expected not {}".format(self._chars))
        else:
            return Parsed(string[0],string[1:],"")

"""
Parsers for combining other parsers
"""

class ParseObjectEither():
    """Object to store the successful result of the or'ing of parsers, if any,
    and which of the parsers succeeded"""
    def __init__(self,result,value):
        if isinstance(result, ParseObjectEither):
            self.result = result.result
            self.value = value + result.value
        else:
            self.result = result
            self.value = value
    def __repr__(self):
        return "Option({}: {})".format(self.value,self.result)

class ParseOr(Parser):
    """Parser that tries 2 parsers and succeeds if either succeeds"""
    def __init__(self, p1, p2):
        self._p1 = p1
        self._p2 = p2

    def parse(self,string):
        result = self._p1(string)
        result.result = ParseObjectEither(result.result,0)
        if result.error:
            result = self._p2(string)
            result.result = ParseObjectEither(result.result,1)
        return result

class ParseObjectList():
    """Object to store the results of multiple parsers concatenated with '&'
    """
    def __init__(self,result):
        if isinstance(result,ParseObjectList):
            self.results = result.results
        elif result == PIgnore:
            self.results = []
        else:
            self.results = [result]

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
        self._p1 = p1
        self._p2 = p2

    def parse(self,string):
        resultl = self._p1(string)
        if resultl.error:
            return resultl
        resultr = self._p2(resultl.left)
        resultl.result = ParseObjectList(resultl.result)
        resultl.result.append(resultr.result)
        return Parsed(resultl.parsed + resultr.parsed,
                      resultr.left, resultr.error,resultl.result)



""" Meta-parsers that take another parser as input """

class Ignore(Parser):
    """Perform the action of another parser, discarding its result but keeping
    errors"""
    def __init__(self,other):
        self._other = other

    def parse(self,string):
        result = self._other.parse(string)
        result.result = PIgnore
        return result

class Maybe(Parser):
    def __init__(self,other):
        self._other = other

    def parse(self,string):
        return (self._other | Parser()).parse(string)

class Many(Parser):
    """Parse zero or more of an item"""
    def __init__(self,other):
        self._other = other

    def parse(self,string):
        result = self._other(string)
        parsed = [result.parsed]
        while not result.error:
            result = self._other.parse(result.left)
            parsed.append(result.parsed)
        return Parsed(''.join(parsed),result.left,"")

class Some(Many):
    def parse(self,string):
        return (self._other & Many(self._other)).parse(string)

"""Common utility parsers"""
class ParseString(Parser):
    def parse(self,string):
        p = Ignore(ParseA('"')) & Many(ParseNot('"')) & Ignore(ParseA('"'))
        result = p(string)
        return result
        
class ParseInt(Parser):
    def parse(self,string):
        result = (Maybe(ParseA('-')) & Some(ParseAny(DIGITS)))(string)
        if not result.error:
            result.result = int(result.parsed)
        return result

class ParseFloat(Parser):
    def parse(self,string):
        p = Maybe(ParseA('-')) & (
            (Many(ParseAny(DIGITS)) & ParseA('.') & Some(ParseAny(DIGITS))) | 
            (Some(ParseAny(DIGITS)) & ParseA('.') & Many(ParseAny(DIGITS))))
        result = p(string)
        if not result.error:
            result.result = float(result.parsed)
        return result

class ParseBool(ParseAny):
    def __init__(self):
        self._chars = ["true","false"]

class Spaces(Parser):
    def parse(self,string):
        p = Ignore(Many(ParseAny(' \t\n')))
        return p(string)

class SpacesAround(Parser):
    def __init__(self,other):
        self._other = other
    def parse(self,string):
        p = Spaces() & self._other & Spaces()
        return p(string)

if __name__ == '__main__':
    print((ParseFloat())('-5.'))
