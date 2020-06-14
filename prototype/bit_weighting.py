import sys
import os
from optparse import OptionParser
import copy
import random

# genprog: Class Rep: you need to write your own class 
# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
import pyverilog.vparser.ast as vast

class OutputAnalyzer(ASTCodeGenerator):
    def __init__(self):
        self.output_bits_length = dict()
        self.assignment_counts = dict()

    def visit(self, ast, repeated=1):

        if ast.__class__.__name__ in ('Output', 'Inout'):
            if ast.width and ast.width.msb.__class__.__name__ == "IntConst": # TODO: fix this, e.g. X = [Y-1:0]
                self.output_bits_length[ast.name] = int(ast.width.msb.value) - int(ast.width.lsb.value) + 1
            else:
                self.output_bits_length[ast.name] = 1
            self.assignment_counts[ast.name] = 0

        #TODO: This weighting assigns each bit in a wire uniform widths. Change it to assign individual
        #      bits their own weights. e.g. if op[7] gets more assignments than op[1], the former should
        #      have a higher weight than the latter.
        if ast.__class__.__name__ in ('NonblockingSubstitution','BlockingSubstitution', 'Assign') and ast.right.var:
            if ast.left.var.__class__.__name__ == "LConcat":
                for tmp in ast.left.var.list:
                    if tmp.name in self.assignment_counts:
                        self.assignment_counts[tmp.name] += repeated * 1
            elif ast.left.var.__class__.__name__ == "Identifier":
                var_name = ast.left.var.name
                if var_name in self.assignment_counts:
                    self.assignment_counts[var_name] += repeated * 1
            elif ast.left.var.__class__.__name__ == "Pointer":
                var_name = ast.left.var.var.name
                if var_name in self.assignment_counts:
                    self.assignment_counts[var_name] += repeated * 1

        for c in ast.children():
            if c.__class__.__name__ == "ForStatement":
                self.visit(c,self.get_repeated_for(c))
            elif repeated != 1:
                self.visit(c,repeated)
            else:
                self.visit(c)

    #TODO: Only supports the format (i=?; i{<,<=}}x; i=i{op}y). Update if needed.
    #      Also does not support nested for loops. It is only an approximation, does not
    #      need very accurate estimations.
    def get_repeated_for(self, ast):
        ret = 1
        if ast.pre.right.var:
            begin = int(ast.pre.right.var.value)
        if ast.cond.__class__.__name__ == "LessThan":
            end = int(ast.cond.right.value)
        elif ast.cond.__class__.__name__ == "LessEq":
            end = int(ast.cond.right.value) + 1
        if ast.post.right:
            step = int(ast.post.right.var.right.value)
        try:
            ret = (end - begin) // step
        except UnboundLocalError:
            print("WARNING: For loop parsing not supported for this Verilog program. Defaulting to a value of 1.")
        return ret

    def assign_weigts(self):
        weights = dict()
        inverted_weights = dict()
        total = 0
        for var in self.assignment_counts:
            if self.assignment_counts[var] != 0:
                total += self.assignment_counts[var]
        for var in self.assignment_counts:
            if self.assignment_counts[var] != 0:
                inverted_weights[var] = 1/(self.assignment_counts[var]/total)
        inverted_total = sum(inverted_weights.values())
        # print(inverted_weights)
        # print(inverted_total)
        for var in inverted_weights:
            weights[var] = inverted_weights[var]/(inverted_total * self.output_bits_length[var])
        return weights

def main():
    INFO = "Verilog code parser"
    USAGE = "Usage: python example_parser.py file ..."

    def showVersion():
        print(INFO)
        print(USAGE)
        sys.exit()

    optparser = OptionParser()
    optparser.add_option("-v","--version",action="store_true",dest="showversion",
                         default=False,help="Show the version")
    optparser.add_option("-I","--include",dest="include",action="append",
                         default=[],help="Include path")
    optparser.add_option("-D",dest="define",action="append",
                         default=[],help="Macro Definition")
    (options, args) = optparser.parse_args()

    filelist = args
    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    codegen = ASTCodeGenerator()


    # parse the files (in filelist) to ASTs (PyVerilog ast)
    ast, directives = parse(filelist,
                            preprocess_include=options.include,
                            preprocess_define=options.define)

    ast.show()
    # print(codegen.visit(ast))
    # print("\n\n")

    outputanalyzer = OutputAnalyzer()
    outputanalyzer.visit(ast)
    # print(outputanalyzer.output_bits_length)
    # print(outputanalyzer.assignment_counts)
    weights = outputanalyzer.assign_weigts()

    f = open("weights.txt", 'w+')
    for var in weights:
        print("Each bit of %s should have a weight of %s." % (var, weights[var]))
        f.write("%s=%s\n" % (var, weights[var]))
    f.close()

    print(outputanalyzer.output_bits_length)
    print(outputanalyzer.assignment_counts)

if __name__ == '__main__':
    main()