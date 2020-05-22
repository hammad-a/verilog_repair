import sys
import os
from optparse import OptionParser
import copy

# genprog: Class Rep: you need to write your own class 
# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
import pyverilog.vparser.ast as vast


"""
Valid mutation operators supported by the algorithm.
"""
VALID_MUTATIONS = ["swap_plus_minus", "increment_identifier"]

"""
Returns a set of line numbers as potential targets for mutations.
"""
class CandidateCollector(ASTCodeGenerator):
    def __init__(self):
        self.my_candidates = set()

    def visit(self, ast):
        if ast.__class__.__name__ in [ 'BlockingSubstitution', 'NonblockingSubstitution' ]:
            self.my_candidates.add(ast.lineno)

        for c in ast.children():
            self.visit(c)

class Mutate(ASTCodeGenerator):

    def __init__(self):
        self.mutation = "null"
        self.mutateAt = -1

    def set_mutation(self, mutation, lineno):
        self.mutation = mutation
        self.mutateAt = lineno
    
    def reset_mutation(self):
        self.mutation = "null"
        self.mutateAt = -1

    def addToBVal(self, bVal, num):
        tmp = int(bVal.split('b')[1], 2)
        numBits = int(bVal.split('\'')[0])
        tmp += num
        tmpstr = ('{0:0'+str(numBits)+'b}').format(tmp)
        if len(tmpstr) > numBits: # drop the most significant bit if the length after incrementing is longer than the number of bits
            tmpstr = tmpstr[len(tmpstr)-numBits:]
        return str(numBits) + "'b" + tmpstr

    def visit(self, ast):

        if self.mutation == "swap_plus_minus":
            if ast.__class__.__name__ == 'NonblockingSubstitution' and ast.right.var:
                if ast.right.var.__class__.__name__ == "Plus" and ast.right.var.lineno == self.mutateAt:
                    new_child = vast.Minus(ast.right.var.left, ast.right.var.right)
                    print("Changing %s on line %s to %s" % (ast.right.var, ast.right.var.lineno, new_child))
                    ast.right.var = new_child
                elif ast.right.var.__class__.__name__ == "Minus" and ast.right.var.lineno == self.mutateAt:
                    new_child = vast.Plus(ast.right.var.left, ast.right.var.right)
                    print("Changing %s on line %s to %s" % (ast.right.var, ast.right.var.lineno, new_child))
                    ast.right.var = new_child
        elif self.mutation == "increment_identifier":
            if ast.__class__.__name__ == 'NonblockingSubstitution':
                my_lvalue = ast.left.var
                my_rvalue = ast.right.var
                if my_lvalue.__class__.__name__ == 'Identifier' and my_rvalue.__class__.__name__ == 'IntConst' and my_rvalue.lineno == self.mutateAt:
                    incrementedVal = self.addToBVal(my_rvalue.value, 1)
                    print("Updating {} from {} to {}".format(my_lvalue.name,
                        my_rvalue.value,
                    incrementedVal))
                    my_rvalue.value = incrementedVal
        elif self.mutation not in VALID_MUTATIONS or self.mutateAt == -1:
            print("Not a valid mutation: %s at line %d" % (self.mutation, self.mutateAt))


        for c in ast.children():
            self.visit(c)

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
    print(codegen.visit(ast))
    print("\n\n")

    candidatecollector = CandidateCollector()
    candidatecollector.visit(ast)

    mutation_op = Mutate()

    attempts = 0
    valids = 0
    for choice in VALID_MUTATIONS:
        for line in candidatecollector.my_candidates:
            mutation_op.set_mutation(choice, line)
            tmp = copy.deepcopy(ast)
            mutation_op.visit(tmp)
            if tmp != ast: # if the mutation was successful
                print(codegen.visit(tmp))
                print("#################\n")
                valids += 1
            attempts += 1
    
    print(valids,attempts)


if __name__ == '__main__':
    main()
