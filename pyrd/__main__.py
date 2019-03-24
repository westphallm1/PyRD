from . import pyrd_grammar
import sys

if __name__=='__main__':
    if len(sys.argv) != 3:
        print("usage: pyrdg /path/to/input.grammar /path/to/output.py".format(
            sys.argv[0]))
        exit(1)
    with open(sys.argv[1]) as gramf:
        to_parse = gramf.read()
        parsed = pyrd_grammar.Grammar().parse(to_parse)
        if parsed:
            print("Grammar parsed sucessfully.")
            parsed.result.gen_code(sys.argv[2])
        else:
            print("Error:",parsed.err(to_parse))
            exit(1)


