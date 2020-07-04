import sys, inspect, subprocess
import os
from optparse import OptionParser
import copy
import random

# genprog: Class Rep: you need to write your own class 
# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyverilog.vparser.parser import parse, NodeNumbering
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
from pyverilog.vparser.plyparser import ParseError
import pyverilog.vparser.ast as vast

AST_CLASSES = []

for name, obj in inspect.getmembers(vast):
    if inspect.isclass(obj):
        AST_CLASSES.append(obj)

# print(AST_CLASSES)
# f = open("ast_classes.txt", "w+")
# for item in AST_CLASSES:
#     f.write(str(item) + "\n")
# f.close()

REPLACE_TARGETS = {} # dict from class to list of classes that are okay to substituite for the original class
for i in range(len(AST_CLASSES)):
    REPLACE_TARGETS[AST_CLASSES[i]] = []
    REPLACE_TARGETS[AST_CLASSES[i]].append(AST_CLASSES[i]) # can always replace with a node of the same type
    for j in range(len(AST_CLASSES)):
        # get the immediate parent classes of both classes, and if the parent if not Node, the two classes can be swapped
        if i != j and inspect.getmro(AST_CLASSES[i])[1] == inspect.getmro(AST_CLASSES[j])[1] and inspect.getmro(AST_CLASSES[j])[1] != vast.Node:
            REPLACE_TARGETS[AST_CLASSES[i]].append(AST_CLASSES[j])
       
# for key in REPLACE_TARGETS:
#     tmp = map(lambda x: x.__name__, REPLACE_TARGETS[key]) 
#     print("Class %s can be replaced by the following: %s" % (key.__name__, list(tmp)))
#     print()

"""
Valid mutation operators supported by the algorithm.
"""
VALID_MUTATIONS = ["swap_plus_minus", "increment_identifier", "decrement_identifier", "increment_rhand_eq", "decrement_rhand_eq",
    "flip_if_cond", "flip_all_sens_edge", "flip_random_sens_edge", "increment_cond_vals", "decrement_cond_vals", "change_identifier_name"]

"""
Valid mutation operators supported by the algorithm.
"""
MUTATIONS_TARGETS = ["BlockingSubstitution", "NonblockingSubstitution", "IfStatement", "SensList", "Eq", "Cond", "Identifier"]

"""
Valid targets for the delete and insert operators.
"""
DELETE_TARGETS = ["IfStatement", "NonblockingSubstitution", "BlockingSubstitution", "ForStatement", "Always", "Case", "CaseStatement", "DelayStatement", "Localparam", "Assign", "Wire"]
INSERT_TARGETS = ["IfStatement", "NonblockingSubstitution", "BlockingSubstitution", "ForStatement", "Always", "Case", "CaseStatement", "DelayStatement", "Localparam", "Assign"]

WRITE_TO_FILE = True

PARENT_OF_GENOME = {}

"""
Returns a set of line numbers as potential targets for mutations.
"""
class CandidateCollector(ASTCodeGenerator):
    def __init__(self):
        self.my_candidates = set()
        self.my_identifiers = set()

    def visit(self, ast):
        if ast.__class__.__name__ in MUTATIONS_TARGETS:
            self.my_candidates.add(ast.lineno)
        if ast.__class__.__name__ in [ 'Port', 'Input', 'Wire' ]:
            self.my_identifiers.add(ast.name)

        for c in ast.children():
            self.visit(c)

class Mutate(ASTCodeGenerator):

    def __init__(self, identifiers):
        self.mutation = "null"
        self.mutateAt = -1
        self.identifiers = identifiers

    def set_mutation(self, mutation, lineno):
        self.mutation = mutation
        self.mutateAt = lineno
    
    def reset_mutation(self):
        self.mutation = "null"
        self.mutateAt = -1

    def visit(self, ast):

        if self.mutation == "swap_plus_minus":
            # TODO: change to include blocking substitution as well?
            if ast.__class__.__name__ == 'NonblockingSubstitution' and ast.right.var:
                if ast.right.var.__class__.__name__ == "Plus" and ast.right.var.lineno == self.mutateAt:
                    new_child = vast.Minus(ast.right.var.left, ast.right.var.right)
                    print("Changing %s on line %s to %s" % (ast.right.var, ast.right.var.lineno, new_child))
                    ast.right.var = new_child
                elif ast.right.var.__class__.__name__ == "Minus" and ast.right.var.lineno == self.mutateAt:
                    new_child = vast.Plus(ast.right.var.left, ast.right.var.right, ast.right.var.lineno)
                    print("Changing %s on line %s to %s" % (ast.right.var, ast.right.var.lineno, new_child))
                    ast.right.var = new_child

        elif self.mutation == "increment_identifier":
            if ast.__class__.__name__ == 'NonblockingSubstitution':
                my_lvalue = ast.left.var
                my_rvalue = ast.right.var
                if my_lvalue.__class__.__name__ == 'Identifier' and my_rvalue.__class__.__name__ == 'IntConst' and my_rvalue.lineno == self.mutateAt:
                    incrementedVal = my_rvalue.value + " + 1"
                    print("Updating %s on line %d from %s to %s" % (my_lvalue.name, my_rvalue.lineno, my_rvalue.value, incrementedVal))
                    my_rvalue.value = incrementedVal
                elif my_lvalue.__class__.__name__ == 'Identifier' and my_rvalue.__class__.__name__ in ['Plus', 'Minus', 'Times', 'Divide', 'Mod']  and my_rvalue.lineno == self.mutateAt:
                    new_child = vast.Plus(my_rvalue, vast.IntConst(1))
                    print("Changing %s on line %s to %s" % (my_rvalue, ast.right.var.lineno, new_child))
                    ast.right.var = new_child

        elif self.mutation == "decrement_identifier":
            if ast.__class__.__name__ == 'NonblockingSubstitution':
                my_lvalue = ast.left.var
                my_rvalue = ast.right.var
                if my_lvalue.__class__.__name__ == 'Identifier' and my_rvalue.__class__.__name__ == 'IntConst' and my_rvalue.lineno == self.mutateAt:
                    decrementedVal = my_rvalue.value + " - 1"
                    print("Updating %s on line %d from %s to %s" % (my_lvalue.name, my_rvalue.lineno, my_rvalue.value, decrementedVal))
                    my_rvalue.value = decrementedVal
                elif my_lvalue.__class__.__name__ == 'Identifier' and my_rvalue.__class__.__name__ in ['Plus', 'Minus', 'Times', 'Divide', 'Mod']  and my_rvalue.lineno == self.mutateAt:
                    new_child = vast.Minus(my_rvalue, vast.IntConst(1))
                    print("Changing %s on line %s to %s" % (my_rvalue, ast.right.var.lineno, new_child))
                    ast.right.var = new_child

        elif self.mutation == "increment_rhand_eq":
            if ast.__class__.__name__ == 'Eq':
                if ast.right.__class__.__name__ == 'IntConst' and ast.right.lineno == self.mutateAt:
                    incrementedVal = ast.right.value + " + 1"
                    print("Changing %s on line %s to %s" % (ast.right, ast.right.lineno, incrementedVal))
                    ast.right.value = incrementedVal

        elif self.mutation == "decrement_rhand_eq":
            if ast.__class__.__name__ == 'Eq':
                if ast.right.__class__.__name__ == 'IntConst' and ast.right.lineno == self.mutateAt:
                    decrementedVal = ast.right.value + " - 1"
                    print("Changing %s on line %s to %s" % (ast.right, ast.right.lineno, decrementedVal))
                    ast.right.value = decrementedVal

        elif self.mutation == "flip_if_cond":
            if ast.__class__.__name__ == 'IfStatement' and ast.lineno == self.mutateAt:
                if ast.cond.__class__.__name__ == "Eq":
                    new_cond = vast.NotEq(ast.cond.left, ast.cond.right, ast.lineno)
                    print("Changing %s on line %s to %s" % (ast.cond, ast.lineno, new_cond))
                    ast.cond = new_cond

        elif self.mutation == "flip_all_sens_edge":
            if ast.__class__.__name__ == 'SensList' and ast.lineno == self.mutateAt:
                for sens in ast.list:
                    newType = random.choice(("posedge", "negedge", "level", "all"))
                    print("Changing sens %s type on line %s from %s to %s" % (sens.sig, ast.lineno, sens.type, newType))
                    sens.type = newType

        elif self.mutation == "flip_random_sens_edge":
            if ast.__class__.__name__ == 'SensList' and ast.lineno == self.mutateAt:
                sens = random.choice(ast.list)
                newType = random.choice(("posedge", "negedge", "level", "all"))
                print("Changing sens %s type on line %s from %s to %s" % (sens.sig, ast.lineno, sens.type, newType))
                sens.type = newType

        elif self.mutation == "increment_cond_vals":
            if ast.__class__.__name__ == "Cond" and ast.lineno == self.mutateAt:
                p = random.random()
                if p > 0.5 and ast.true_value.__class__.__name__ == "IntConst":
                    incrementedVal = ast.true_value.value + " + 1"
                    print("Changing the true value %s on line %s to %s" % (ast.true_value, ast.true_value.lineno, incrementedVal))
                    ast.true_value.value = incrementedVal
                elif ast.false_value.__class__.__name__ == "IntConst":
                    incrementedVal = ast.false_value.value + " + 1"
                    print("Changing the false value %s on line %s to %s" % (ast.false_value, ast.false_value.lineno, incrementedVal))
                    ast.false_value.value = incrementedVal

        elif self.mutation == "decrement_cond_vals":
            if ast.__class__.__name__ == "Cond" and ast.lineno == self.mutateAt:
                p = random.random()
                if p > 0.5 and ast.true_value.__class__.__name__ == "IntConst":
                    decrementedVal = ast.true_value.value + " - 1"
                    print("Changing the true value %s on line %s to %s" % (ast.true_value, ast.true_value.lineno, decrementedVal))
                    ast.true_value.value = decrementedVal
                elif ast.false_value.__class__.__name__ == "IntConst":
                    decrementedVal = ast.false_value.value + " - 1"
                    print("Changing the false value %s on line %s to %s" % (ast.false_value, ast.false_value.lineno, decrementedVal))
                    ast.false_value.value = decrementedVal
        
        elif self.mutation == "change_identifier_name":
            if ast.__class__.__name__ == "Identifier" and ast.lineno == self.mutateAt:
                newName = random.choice(self.identifiers)
                print("Changing the identifier name at line %s from %s to %s" % (ast.lineno, ast.name, newName))
                ast.name = newName

        elif self.mutation not in VALID_MUTATIONS or self.mutateAt == -1:
            print("Not a valid mutation: %s at line %d" % (self.mutation, self.mutateAt))


        for c in ast.children():
            self.visit(c)

class MutationOp(ASTCodeGenerator):

    def __init__(self, popsize):
        self.numbering = NodeNumbering()
        self.popsize = popsize
        self.patch_list = {} # dictionary from genome number to the patch_list
        for i in range(self.popsize): self.patch_list[i] = []
        # temporary variables used for storing data for the mutation operators
        self.tmp_node = None 
        self.deletable_nodes = []
        self.insertable_nodes = []
        self.replaceable_nodes = []
        self.node_class_to_replace = None
        self.stmt_nodes = []
        self.max_node_id = -1

    """ 
    Replace node_x with new_expresssion in the AST.
    """
    def replace_with_expression(self, ast, old_node_id, new_expression):
        attr = vars(ast)
        for key in attr: # loop through all attributes of this AST
            if attr[key].__class__ in AST_CLASSES: # for each attribute that is also an AST
                if attr[key].node_id == old_node_id:
                    self.get_ast_replacement(attr[key], new_expression)
                    attr[key] = self.ast_from_text
                    self.ast_from_text = None # reset self.ast_from_text for the next mutation
            elif attr[key].__class__ in [list, tuple]: # for attributes that are lists or tuples
                for i in range(len(attr[key])): # loop through each AST in that list or tuple
                    tmp = attr[key][i]
                    if tmp.__class__ in AST_CLASSES and tmp.node_id == old_node_id:
                        self.get_ast_replacement(tmp, new_expression)
                        attr[key][i] = self.ast_from_text
                        self.ast_from_text = None # reset self.ast_from_text for the next mutation

        for c in ast.children():
            if c: self.replace_with_expression(c, old_node_id, new_expression) 

    # not used anymore!        
    def get_ast_replacement(self, old, expression):
        self.make_ast_from_text(expression)
        new_ast = self.ast_from_text

        def fix_lineno(a):
            a.lineno = old.lineno
            
            for c1 in a.children():
                if c1: fix_lineno(c1)

        fix_lineno(self.ast_from_text) # fix the line numbers to match the line being replaced

    """
    Update the line number of an AST that has been inserted or replaced.
    """
    def fix_lineno(self, ast, orig_ast):
        ast.lineno = orig_ast.lineno
            
        for c in ast.children():
            if c: self.fix_lineno(c, orig_ast)

    """ 
    Replaces the node corresponding to old_node_id with new_node.
    """
    def replace_with_node(self, ast, old_node_id, new_node):
        attr = vars(ast)
        for key in attr: # loop through all attributes of this AST
            if attr[key].__class__ in AST_CLASSES: # for each attribute that is also an AST
                if attr[key].node_id == old_node_id:
                    attr[key] = copy.deepcopy(new_node)
                    return
            elif attr[key].__class__ in [list, tuple]: # for attributes that are lists or tuples
                for i in range(len(attr[key])): # loop through each AST in that list or tuple
                    tmp = attr[key][i]
                    if tmp.__class__ in AST_CLASSES and tmp.node_id == old_node_id:
                        attr[key][i] = copy.deepcopy(new_node)
                        return

        for c in ast.children():
            if c: self.replace_with_node(c, old_node_id, new_node)
    
    """
    Deletes the node with the node_id provided, if such a node exists.
    """
    def delete_node(self, ast, node_id):
        attr = vars(ast)
        for key in attr: # loop through all attributes of this AST
            if attr[key].__class__ in AST_CLASSES: # for each attribute that is also an AST
                if attr[key].node_id == node_id:
                    attr[key] = None
            elif attr[key].__class__ in [list, tuple]: # for attributes that are lists or tuples
                for i in range(len(attr[key])): # loop through each AST in that list or tuple
                    tmp = attr[key][i]
                    if tmp.__class__ in AST_CLASSES and tmp.node_id == node_id:
                        attr[key][i] = None

        for c in ast.children():
            if c: self.delete_node(c, node_id)
    
    """
    Inserts node with node_id after node with after_id.
    """
    def insert_stmt_node(self, ast, node, after_id): 
        if ast.__class__.__name__ == "Block":
            insert_point = -1
            for i in range(len(ast.statements)):
                stmt = ast.statements[i]
                if stmt and stmt.node_id == after_id:
                    insert_point = i + 1
                    break
            if insert_point != -1:
                print(ast.statements)
                ast.statements.insert(insert_point, copy.deepcopy(node))
                print(ast.statements)
                return

        for c in ast.children():
            if c: self.insert_stmt_node(c, node, after_id)
    
    """
    Gets the node matching the node_id provided, if one exists, by storing it in the temporary node variable.
    Used by the insert and replace operators.
    """    
    def get_node_from_ast(self, ast, node_id):
        if ast.node_id == node_id:
            self.tmp_node = ast
        
        for c in ast.children():
            if c: self.get_node_from_ast(c, node_id)

    """
    Gets a list of all nodes that can be deleted.
    """
    def get_deletable_nodes(self, ast):
        if ast.__class__.__name__ in DELETE_TARGETS:
            self.deletable_nodes.append(ast.node_id)

        for c in ast.children():
            if c: self.get_deletable_nodes(c) 

    """
    Gets a list of all nodes that can be inserted into to a begin ... end block.
    """
    def get_insertable_nodes(self, ast):
        if ast.__class__.__name__ in INSERT_TARGETS:
            self.insertable_nodes.append(ast.node_id)

        for c in ast.children():
            if c: self.get_insertable_nodes(c) 
    
    """
    Gets the class of the node being replaced in a replace operation. 
    This class is used to find potential sources for the replacement.
    """
    def get_node_to_replace_class(self, ast, node_id):
        if ast.node_id == node_id:
            self.node_class_to_replace = ast.__class__

        for c in ast.children():
            if c: self.get_node_to_replace_class(c, node_id)
    
    """
    Gets all nodes that compatible to be replaced with a node of the given class type. 
    These nodes are potential sources for replace operations.
    """
    def get_replaceable_nodes_by_class(self, ast, node_type):
        if ast.__class__ in REPLACE_TARGETS[node_type]:
            self.replaceable_nodes.append(ast.node_id)

        for c in ast.children():
            if c: self.get_replaceable_nodes_by_class(c, node_type)

    """
    Gets all nodes that are found within a begin ... end block. 
    These nodes are potential destinations for insert operations.
    """
    def get_nodes_in_block_stmt(self, ast):
        if ast.__class__.__name__ == "Block":
            if len(ast.statements) == 0: # if empty block, return the node id for the block (so that a node can be inserted into the empty block)
                self.stmt_nodes.append(ast.node_id)
            else:
                for c in ast.statements:
                    if c: self.stmt_nodes.append(c.node_id)
        
        for c in ast.children():
            if c: self.get_nodes_in_block_stmt(c) 
    
    """
    The delete, insert, and replace operators to be called from outside the class.
    Note: node_id, with_id, and after_id would not be none if we are trying to regenerate AST from patch list, and would be none for a random mutation.
    """
    def delete(self, ast, node_id=None):
        if node_id == None:
            self.get_deletable_nodes(ast) # get all nodes that can be deleted without breaking the AST / syntax
            if len(self.deletable_nodes) == 0: # if no nodes can be deleted, return without attepmting delete
                print("Delete operation not possible. Returning with no-op.")
                return 
            node_id = random.choice(self.deletable_nodes) # choose a random node_id to delete

        print("Deleting node with id %s\n" % node_id)
        self.delete_node(ast, node_id) # delete the node corresponding to node_id
        self.numbering.renumber(ast) # renumber nodes
        self.max_node_id = self.numbering.c # reset max_node_id
        self.numbering.c = -1
        self.deletable_nodes = [] # reset deletable nodes for the next delete operation
        # self.patch_list[genome_num].append("delete(%s)" % node_id) # update patch list
    
    def insert(self, ast, node_id=None, after_id=None):
        if node_id == None and after_id == None:
            self.get_insertable_nodes(ast) # get all nodes with a type that is suited to insertion in block statements -> src
            self.get_nodes_in_block_stmt(ast) # get all nodes within a block statement -> dest
            if len(self.insertable_nodes) == 0 or len(self.stmt_nodes) == 0: # if no insertable nodes exist, exit gracefully
                print("Insert operation not possible. Returning with no-op.")
                return
            after_id = random.choice(self.stmt_nodes) # choose a random src and dest
            node_id = random.choice(self.insertable_nodes)
        self.get_node_from_ast(ast, node_id) # get the node associated with the src node id
        print("Inserting node with id %s after node with id %s\n" % (node_id, after_id))
        self.insert_stmt_node(ast, self.tmp_node, after_id) # perform the insertion
        self.numbering.renumber(ast) # renumber nodes
        self.max_node_id = self.numbering.c # reset max_node_id
        self.numbering.c = -1
        self.insertable_nodes = [] # reset the temporary variables
        self.tmp_node = None
        # self.patch_list[genome_num].append("insert(%s,%s)" % (node_id, after_id)) # update patch list
    
    # TODO: Possible bug -> sometimes replacement nodes are not compatible in terms of their classes?
    def replace(self, ast, node_id=None, with_id=None):
        if node_id == None:
            if self.max_node_id == -1: # if max_id is not know yet, traverse the AST to find the number of nodes -- needed to pick a random id to replace
                self.numbering.renumber(ast)
                self.max_node_id = self.numbering.c
                self.numbering.c = -1 # reset the counter for numbering
            node_id = random.randint(0,self.max_node_id) # get random node id to replace
        print("Node to replace id: %s" % node_id)

        if with_id == None: 
            self.get_node_to_replace_class(ast, node_id) # get the class of the node associated with the random node id
            print("Node to replace class: %s" % self.node_class_to_replace)
            if self.node_class_to_replace == None: # if the node does not exist (could have been a part of gen i but not i-1) -> TODO: is this still needed?
                return
            self.get_replaceable_nodes_by_class(ast, self.node_class_to_replace) # get all valid nodes that have a class that could be substituted for the original node's class
            if len(self.replaceable_nodes) == 0: # if no replaceable nodes exist, exit gracefully
                print("Replace operation not possible. Returning with no-op.")
                return
            with_id = random.choice(self.replaceable_nodes) # get a random node id from the replaceable nodes
        self.get_node_from_ast(ast, with_id) # get the node associated with with_id
        
        print("Replacing node id %s with node id %s" % (node_id,with_id))
        self.replace_with_node(ast, node_id, self.tmp_node) # perform the replacement
        self.tmp_node = None # reset the temporary variables
        self.replaceable_nodes = []
        self.node_class_to_replace = None
        self.numbering.renumber(ast) # renumber nodes
        self.max_node_id = self.numbering.c # update max_node_id
        self.numbering.c = -1
        # self.patch_list[genome_num].append("replace(%s,%s)" % (node_id, with_id)) # update patch list
    
    def ast_from_patchlist(self, ast, patch_list):
        for m in patch_list:
            operator = m.split('(')[0]
            operands = m.split('(')[1].replace(')','').split(',')
            print(operator, operands)
            if operator == "replace":
                self.replace(ast, int(operands[0]), int(operands[1]))
            elif operator == "insert":
                self.insert(ast, int(operands[0]), int(operands[1]))
            elif operator == "delete":
                self.delete(ast, int(operands[0]))
            else:
                print("Invalid operator in patch list: %s" % m)
        return ast

def tournament_selection(pop):
    # TODO: implement this!
    return random.choice(pop)

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
    print("\n")

    # Generate the bit-weights
    srcFile = sys.argv[1]
    bashCmd = ["python3", "bit_weighting.py", srcFile]
    process = subprocess.run(bashCmd, capture_output=True, check=True)
    # print(process.stdout, process.stderr) # if there is a CalledProcessError, uncomment this to see the contents of stderr

    GENS = 0
    POPSIZE = 2

    mutation_op = MutationOp(POPSIZE)

    pop = []
    pop.append([])
    # print(pop)

        
    failed = 0
    fpatches = []

    tmp = ['delete(74)', 'insert(65,65)', 'replace(44,82)']
    patch = copy.deepcopy(ast)
    mutation_op.ast_from_patchlist(patch, tmp)
    patch.show()
    print(codegen.visit(patch))



    # for i in range(GENS): # for each generation
    #     _children = []

    #     while len(_children) < POPSIZE:
    #         j = len(_children)
    #         parent = tournament_selection(pop)
    #         child = copy.deepcopy(parent)

    #         f = open("candidate.v", "w+")
    #         p = random.random()
    #         if p >= 0.5:
    #             mutation_op.replace(child, j)
    #         elif p >= 0.25:
    #             mutation_op.delete(child, j)
    #         else:
    #             mutation_op.insert(child, j)
    #         ast.show()
    #         rslt = codegen.visit(child)
    #         print(rslt)
    #         f.write(rslt)
    #         f.close()
    #         print("For genome %d:" % j, mutation_op.patch_list[j], len(mutation_op.patch_list[j]))

    #         _children.append(child)
    #         PARENT_OF_GENOME[child] = parent
        



        # for j in range(POPSIZE): # for each genome
        #     genome = pop[j]
        #     if i > 0: PARENT_OF_GENOME[j] = copy.deepcopy(genome)
        #     f = open("candidate.v", "w+")
        #     p = random.random()
        #     if p >= 0.5:
        #         mutation_op.replace(genome, j)
        #     elif p >= 0.25:
        #         mutation_op.delete(genome, j)
        #     else:
        #         mutation_op.insert(genome, j)
        #     ast.show()
        #     rslt = codegen.visit(genome)
        #     print(rslt)
        #     f.write(rslt)
        #     f.close()
        #     print("For genome %d:" % j, mutation_op.patch_list[j], len(mutation_op.patch_list[j]))
        #     print()

        #     # re-parse the written candidate to check for syntax errors -> zero fitness if the candidate does not compile
        #     try:
        #         ast, directives = parse(["candidate.v"],
        #                             preprocess_include=options.include,
        #                             preprocess_define=options.define)
        #     except ParseError:
        #         failed += 1
    
    # print("%s candidates failed to compile" % failed)

    for i in pop: print(codegen.visit(i))

    # bashCmd = ["python3", "fitness.py", "../benchmarks/first_counter_overflow/oracle.txt", "../benchmarks/first_counter_overflow/output.txt", "weights.txt", "static"]
    # process = subprocess.run(bashCmd, capture_output=True, check=True)
    # print(process.stdout, process.stderr)

    # output, error = process.communicate()
    # print(output)

    # candidatecollector = CandidateCollector()
    # candidatecollector.visit(ast)

    # mutation_op = Mutate(list(candidatecollector.my_identifiers))

    # try:
    #     dirName = os.getcwd()+"/repair_candidates"
    #     os.mkdir(dirName)
    #     print("Directory " , dirName ,  " created ") 
    # except:
    #     print("Directory " , dirName ,  " already exists")

    # depth_edits = 1
    # try_all_mutations(mutation_op, list(candidatecollector.my_candidates), codegen, ast, depth_edits)

    # try_random_mutations(mutation_op, list(candidatecollector.my_candidates), codegen, ast, 1000)

def try_all_mutations(mutation_op, candidates, codegen, ast, depth, uniq=set()):
    for choice in VALID_MUTATIONS:
        for line in candidates:
            mutation_op.set_mutation(choice, line)
            tmp = copy.deepcopy(ast)
            mutation_op.visit(tmp)
            mutation_op.reset_mutation()
            if tmp != ast: # if the mutation was successful
                uniq.add(tmp)
                if depth > 1:
                    try_all_mutations(mutation_op, candidates, codegen, tmp, depth - 1)

    if depth == 1:
        for tmp in uniq:
            print(codegen.visit(tmp))
            print("#################\n")
        print("A total of %d mutations were performed." % (len(uniq)))


def try_random_mutations(mutation_op, candidates, codegen, ast, maxIters):
    uniq = set()
    for i in range(maxIters):
        # choose a random mutation and line; might not be a valid mutation
        choice = random.choice(VALID_MUTATIONS)
        line = random.choice(candidates)
        mutation_op.set_mutation(choice, line)
        tmp = copy.deepcopy(ast)
        mutation_op.visit(tmp)
        mutation_op.reset_mutation()
        if tmp != ast: # if the mutation was successful and/or resulted in a different ast
            uniq.add(tmp)
    
    # cand_num = 0
    # for tmp in uniq:
    #     rslt = codegen.visit(tmp)
    #     print(rslt)
    #     print("#################\n")
    #     if WRITE_TO_FILE:
    #         outf = open("./repair_candidates/candidate_"+str(cand_num)+".v","w+")
    #         outf.write(str(rslt))
    #         outf.close()
    #     cand_num += 1

    print("A total of %d mutations were successful out of %d attempted mutations." % (len(uniq), maxIters))

if __name__ == '__main__':
    main()
