from pyrd import *

def IgnoreSp(parser):
   return Ignore(SpacesAround(parser)) 

class ParseArray(Parser):
    def parse(self,string):
        result = (IgnoreSp(ParseA("[")) & 
                  ParseElems() & 
                  IgnoreSp(ParseA("]")))(string)
        return result

class ParseElems(Parser):
    def parse(self,string):
        result = ((ParseValue() & IgnoreSp(ParseA(',')) & ParseElems()) | 
                   ParseValue())(string)
        return result

class ParseObject(Parser):
    def parse(self, string):
        result = (IgnoreSp(ParseA("{")) &
                  ParsePairs() &
                  IgnoreSp(ParseA("}")))(string)
        return result

class ParsePairs(Parser):
    def parse(self, string):
        result = ((ParsePair() & IgnoreSp(ParseA(',')) & ParsePairs()) | 
                   ParsePair())(string)
        if result:
            if result.result.value == 1:
                #extract the pair from its Option object
                result.result = result.result.result
            else:
                #combine the new dictionary with the existing one
                new, old = result.result.result
                new.update(old)
                result.result = new
        return result

class ParsePair(Parser):
    def parse(self, string):
        result = (ParseString() & IgnoreSp(ParseA(':')) & 
                 ParseValue())(string)
        if result:
            result.result = {result.result[0]:result.result[1]}
        return result

class ParseValue(Parser):
    def parse(self,string):
        result = (ParseInt() | ParseFloat() | 
                  ParseString() | ParseBool() |
                  ParseArray())(string)
        # oh god
        if result:
            result.result = result.result.result
        return result


if __name__ == '__main__':
    print(ParsePairs()('"foo":5,"bar":6,"baz": 7'))
