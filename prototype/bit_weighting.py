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

    def visit(self, ast):
        if ast.__class__.__name__ == "Output":
            if ast.width:
                self.output_bits_length[ast.name] = int(ast.width.msb.value) - int(ast.width.lsb.value) + 1
            else:
                self.output_bits_length[ast.name] = 1
            self.assignment_counts[ast.name] = 0

        if ast.__class__.__name__ in ('NonblockingSubstitution','BlockingSubstitution') and ast.right.var:
            var_name = ast.left.var.name
            if var_name in self.assignment_counts:
                self.assignment_counts[var_name] += 1

        for c in ast.children():
            self.visit(c)

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

if __name__ == '__main__':
    main()