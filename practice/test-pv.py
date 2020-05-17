from __future__ import absolute_import
from __future__ import print_function
import sys
import os
from optparse import OptionParser
# genprog: Class Rep: you need to write your own class 
# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pyverilog.utils.version
from pyverilog.vparser.parser import parse
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator


class CandidateCollector(ASTCodeGenerator):
    def __init__(self):
        self.my_candidates = set()

    def visit(self, ast):
        if ast.__class__.__name__ in [ 'Port', 'Input', 'Wire' ]:
            self.my_candidates.add(ast.name)

        for c in ast.children():
            self.visit(c)


class FixCollector(ASTCodeGenerator):
    def __init__(self):
        self.my_fixes = []

    def visit(self, ast):
        if ast.__class__.__name__ in [ 'Identifier' ]:
            self.my_fixes.append(ast)

        for c in ast.children():
            self.visit(c)


#custom visitor class that updates expressions of the form:
#   symbolName <= x
# to become
#   symbolName <= x+1
class CrapVisitor(ASTCodeGenerator):
    def visit(self, ast):
        #ast is node 
        #print(ast.__class__.__name__)

        #  Expressions with "<=" are 'nonblockingsubstitutions' in the
        #  abstract syntax
        if ast.__class__.__name__ == 'NonblockingSubstitution':
            # this ast node type has left and right fields, each of
            # which contains a var field to refer to:
            #  left.var: the thing being assigned to
            #  right.var: the thing that gets assigned from
            my_lvalue = ast.left.var
            my_rvalue = ast.right.var

            # now, we only want expressions that have an identifier on
            # the left (i.e., a net name) and a int constant on the
            # right (some [0-9]+)
            if my_lvalue.__class__.__name__ == 'Identifier' \
                    and my_rvalue.__class__.__name__ == 'IntConst':
                #print("Updating {} from {} to {}".format(my_lvalue.name,
                #    my_rvalue.value,
                #    int(my_rvalue.value)+1))
                # apparently, this ast structure stores everything as
                # strings, we to increment, we coerce to an int, add 1,
                # then coerce back to a string
                #my_rvalue.value = str( int(my_rvalue.value) + 1 )
                pass


            

        #if ast.__class__.__name__ == "IntConst":
        #    print("Found int const {}".format(ast.value))
        for c in ast.children():
            self.visit(c)
     



def main():
    INFO = "Verilog code parser"
    VERSION = pyverilog.utils.version.VERSION
    USAGE = "Usage: python example_parser.py file ..."

    def showVersion():
        print(INFO)
        print(VERSION)
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


    # parse the files (in filelist) to ASTs (PyVerilog ast)
    ast, directives = parse(filelist,
                            preprocess_include=options.include,
                            preprocess_define=options.define)
    
    #ast.show()
    #for lineno, directive in directives:
    #    print('Line %d : %s' % (lineno, directive))
    print( "!!")
    print(ast.children()[0].children())  
    print ("!!")

    ast.show()

    candidatecollector = CandidateCollector()
    candidatecollector.visit(ast)
    #print(candidatecollector.my_candidates)

    fixcollector = FixCollector()
    fixcollector.visit(ast)
    #print(fixcollector.my_fixes)

#    crapvisitor = CrapVisitor()
#    print(crapvisitor.visit(ast))

    codegen = ASTCodeGenerator()
    rep_num=0

    try:
        dirName = os.getcwd()+"/pv_candidates"
        os.mkdir(dirName)
        print("Directory " , dirName ,  " created ") 
    except:
        print("Directory " , dirName ,  " already exists")

    for f in fixcollector.my_fixes:
        for c in candidatecollector.my_candidates:
            old_id = f.name
            f.name = c


            print('Repair # {}'.format(rep_num))
            print('Changing {} to {}'.format(old_id, c))

            rslt = codegen.visit(ast)
            print(rslt)

            outf = open("./pv_candidates/candidate_"+str(rep_num)+".v","w+")
            outf.write(str(rslt))
            outf.close()

            print('$$$$$$$$$')

            f.name = old_id
            rep_num = rep_num+1

if __name__ == '__main__':
    main()
