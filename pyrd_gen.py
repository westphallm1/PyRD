"""Generate a pyrd parser for a given pyrd grammar"""
from pyrd import * 
from templates import *
import sys
import re
import logging

def id2class(id_):
    return ''.join([id_[0].upper(),id_[1:]])
""" Storage classes for the results of parsing various types """
class LexResult():
    used_ids = set()
    def __init__(self,index,choice):
        self.index = index
        self.choice = choice
        if self.index == 0:
            LexResult.used_ids.add(self.choice)

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

    def check_left_recursion(self,id_):
        if self.index == 0 and self.choice == id_:
            logging.error("Rule {} is left-recursive! Please refactor grammar".
                    format(self.choice))

    def check_right_recursion(self,id_):
        return self.index == 0 and self.choice == id_

class SeqResult():
    def __init__(self,lexers,function):
        self.lexers = lexers
        self.function = function
        self.right_recursive = False

    def __repr__(self):
        lexers = '\n'.join('      {}'.format(l) for l in self.lexers)
        return "Sequence(function={{{}}},lexers=\n{})".format(
                    self.function,lexers)

    def gen_parser(self):
        parsers = ' & '.join([l.gen_parser() for l in self.lexers])
        if self.right_recursive:
            parsers = '({}).rr()'.format(parsers)
        return parsers

    def gen_rr(self,idx):
        if not self.right_recursive:
            return ""
        ids = []
        for i,l in enumerate(self.lexers):
            line = l.gen_handler()
            if line:
                ids.append(line.format(i))
        ids = ('\n'+' '*16).join(ids)
        return RR_CHOICE_TEMPLATE.format(IDS=ids,FUNCTION=self.function,IDX=idx)

    def gen_handler(self,idx):
        if self.right_recursive:
            function ="return self.handle_rr(parsed_choice)\n"
            return CHOICE_TEMPLATE.format(IDS='',FUNCTION=function,IDX=idx)
        ids = []
        for i,l in enumerate(self.lexers):
            line = l.gen_handler()
            if line:
                ids.append(line.format(i))
        ids = ('\n'+' '*12).join(ids)
        return CHOICE_TEMPLATE.format(IDS=ids,FUNCTION=self.function,IDX=idx)

    def check_left_recursion(self,id_):
        self.lexers[0].check_left_recursion(id_)

    def check_right_recursion(self,id_):
        self.right_recursive = self.lexers[-1].check_right_recursion(id_)


class RuleResult():
    defined_ids = set()
    def __init__(self,id_,sequences):
        self.id = id_
        self.sequences = sequences
        RuleResult.defined_ids.add(self.id)

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
            parsers.append(sequence.gen_handler(i))

        return HANDLER_TEMPLATE.format(CODE=''.join(parsers))

    def gen_rr(self):
        handlers = []
        for i,sequence in enumerate(self.sequences): 
            handlers.append(sequence.gen_rr(i))

        if any(handlers):
            return RIGHT_RECURSIVE_TEMPLATE.format(CODE=''.join(handlers))
        return ""

    def gen_code(self):
        parser = self.gen_parser()
        handler = self.gen_handler()
        handler_rr = self.gen_rr()
        code = CLASS_TEMPLATE.format(ID=id2class(self.id),
                HANDLER=handler, HANDLER_RR=handler_rr, PARSER=parser)
        return code

    def check_left_recursion(self):
        [seq.check_left_recursion(self.id) for seq in self.sequences]

    def check_right_recursion(self):
        [seq.check_right_recursion(self.id) for seq in self.sequences]


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
        handlers = [r.gen_handler() for r in self.rules]
        return handlers

    def gen_code(self,path):
        self.check_errors()
        self.optimize()
        classes = [r.gen_code() for r in self.rules]
        with open(path,'w') as outpy:
            outpy.write(PREFIX)
            for class_ in classes:
                outpy.write(class_)
            outpy.write(self.suffix) 

    def optimize(self):
        self.check_right_recursion()

    def check_errors(self):
        self.check_left_recursion()
        self.check_id_defs()

    def check_left_recursion(self):
        [r.check_left_recursion() for r in self.rules]

    def check_right_recursion(self):
        [r.check_right_recursion() for r in self.rules]

    def check_id_defs(self):
        undefined = LexResult.used_ids - RuleResult.defined_ids
        unused = RuleResult.defined_ids - LexResult.used_ids
        if undefined:
            logging.error("The following ids are used but not defined: {}"
                    .format(', '.join(list(undefined))))
        if unused:
            logging.warning("The following ids are defined but not used: {}"
                    .format(', '.join(list(unused))))
