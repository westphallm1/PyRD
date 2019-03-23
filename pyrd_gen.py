"""Generate a pyrd parser for a given pyrd grammar"""
from pyrd import * 
from pyrd_grammar import *
from templates import *
import sys
import re
def id2class(id_):
    return ''.join([id_[0].upper(),id_[1:]])
""" Storage classes for the results of parsing various types """
class LexResult():
    def __init__(self,result):
        self.index = result.index
        self.choice = result.choice

    def __repr__(self):
        format_ = ["Id({})",'String("{}")',"Regex(/{}/)"][self.index]
        return format_.format(self.choice)

    def gen_parser(self):
        if self.index == 0:
            # generate an id parser -- eg a parser of another class
            return id2class(self.choice)+'()'
        elif self.index == 1:
            return 'ParseStr("""{}""")'.format(self.choice)
        elif self.index == 2:
            return 'ParseRE(r"""{}""")'.format(self.choice)

    def gen_handler(self):
        if self.index == 0:
            return "{} = parsed_choice.choice[{{}}]".format(self.choice)
        return None

class SeqResult():
    def __init__(self,lexers,function):
        self.lexers = lexers
        self.function = function

    def __repr__(self):
        lexers = '\n'.join('      {}'.format(l) for l in self.lexers)
        return "Sequence(function={{{}}},lexers=\n{})".format(
                    self.function,lexers)

    def gen_parser(self):
        return ' & '.join([l.gen_parser() for l in self.lexers])

    def gen_handler(self):
        ids = []
        for i,l in enumerate(self.lexers):
            line = l.gen_handler()
            if line:
                ids.append(line.format(i))
        ids = ('\n'+' '*12).join(ids)
        return CHOICE_TEMPLATE.format(IDS=ids,FUNCTION=self.function)


class RuleResult():
    def __init__(self,id_,sequences):
        self.id = id_
        self.sequences = sequences

    def __repr__(self):
        seqs = '\n'.join('    {}'.format(s) for s in self.sequences)
        return "Rule(id={},sequences=\n{})".format(self.id,seqs)

    def gen_parser(self):
        parsers = [s.gen_parser() for s in self.sequences]
        parser = '|\n        '.join(parsers)
        return PARSE_TEMPLATE.format(PARSERS=parser)

    def gen_handler(self):
        parsers = []
        for i,sequence in enumerate(self.sequences): 
            parsers.append(sequence.gen_handler().format(i))

        return HANDLER_TEMPLATE.format(CODE=''.join(parsers))

    def gen_code(self):
        parser = self.gen_parser()
        handler = self.gen_handler()
        code = CLASS_TEMPLATE.format(ID=id2class(self.id),
                HANDLER=handler, PARSER=parser)
        return code

class GrammarResult():
    def __init__(self,rules,suffix):
        self.rules = rules
        self.suffix=suffix

    def __repr__(self):
        rules = '\n'.join('  {}'.format(r) for r in self.rules)
        return "Grammar(rules=\n{})".format(rules)

    def gen_parser(self):
        parsers = [r.gen_parser() for r in self.rules]
        return parsers

    def gen_handler(self):
        handlers  = [r.gen_handler() for r in self.rules]
        return handlers

    def gen_code(self,path):
        with open(path,'w') as outpy:
            outpy.write(PREFIX)
            classes = [r.gen_code() for r in self.rules]
            for class_ in classes:
                outpy.write(class_)
            outpy.write(self.suffix) 
