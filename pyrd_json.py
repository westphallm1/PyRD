from pyrd import *
import sys

class Array(Parser):
    def parse(self, string):
        Parser.PARSES +=1
        parsed = (Delim("[") & 
                  Elems() & 
                  Delim("]")).parse(string)
        if parsed:
            parsed.result = parsed.result[0][::-1]
        return parsed 

class Elems(Parser):
    def parse(self, string):
        Parser.PARSES +=1
        parsed = (Value() & Delim(',') & Elems() | 
                  Value()).parse(string)
        if parsed:
            if parsed.result.index == 1:
                parsed.result = [parsed.result.result]
            else:
                #append the new object to the existing list
                value, elems = parsed.result.result
                elems.append(value)
                parsed.result = elems
        return parsed 

class Object(Parser):
    def parse(self, string):
        Parser.PARSES +=1
        parsed = (Delim("{") &
                  Pairs() &
                  Delim("}")).parse(string)
        if parsed:
            parsed.result = parsed.result[0]
        return parsed

class Pairs(Parser):
    def parse(self, string):
        Parser.PARSES +=1
        parsed = ((Pair() & Delim(',')) & Pairs() | 
                   Pair()).parse(string)
        if parsed:
            if parsed.result.index == 1:
                #extract the value from its Option object
                parsed.result = parsed.result.result
            else:
                #append the new object to the existing list
                pair, pairs = parsed.result.result
                pair.update(pairs)
                parsed.result = pair
        return parsed 

class Pair(Parser):
    def parse(self, string):
        Parser.PARSES +=1
        parsed = (String() & Delim(':') & 
                 Value()).parse(string)
        if parsed:
            parsed.result = {parsed.result[0]:parsed.result[1]}
        return parsed

class Null(ParseStr):
    def __init__(self):
        self._chars = "null"

    def parse(self, string):
        Parser.PARSES +=1
        parsed = super().parse(string)
        if parsed:
            parsed.result = None
        return parsed

class Value(Parser):
    def parse(self, string):
        Parser.PARSES +=1
        result = (Int()    | Float() | 
                  String() | Bool()  |
                  Array()  | Null()  |
                  Object()).parse(string)
        if result:
            result.result = result.result.result
        else:
            result.error = "Expected a value"
            result.left = string
        return result


if __name__ == '__main__':
    with open(sys.argv[1]) as jsonf:
        to_parse = jsonf.read()
        parsed = Value().parse(to_parse)
        if parsed:
            print(parsed.result)
        else:
            print(parsed)
        print(Parser.PARSES)
