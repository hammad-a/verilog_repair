import sys, inspect, subprocess
import os
from optparse import OptionParser
import copy
import random
import time 
from datetime import datetime
import math

# genprog: Class Rep: you need to write your own class 
# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pyverilog.vparser.parser import parse, NodeNumbering
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator
from pyverilog.vparser.plyparser import ParseError
import pyverilog.vparser.ast as vast

import fitness, fitness_v2

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
Valid targets for the delete and insert operators.
"""
DELETE_TARGETS = ["IfStatement", "NonblockingSubstitution", "BlockingSubstitution", "ForStatement", "Always", "Case", "CaseStatement", "DelayStatement", "Localparam", "Assign"]
INSERT_TARGETS = ["IfStatement", "NonblockingSubstitution", "BlockingSubstitution", "ForStatement", "Always", "Case", "CaseStatement", "DelayStatement", "Localparam", "Assign"]

WRITE_TO_FILE = True

GENOME_FITNESS_CACHE = {}

SRC_FILE = None
TEST_BENCH = None
ORACLE = None
GENS = 5
POPSIZE = 200
RESTARTS = 1
FAULT_LOC = True
CONTROL_FLOW = True
LIMIT_TRANSITIVE_DEPENDENCY_SET = False
DEPENDENCY_SET_MAX = 5
REPLACEMENT_RATE = 1/3
DELETION_RATE = 1/3
INSERTION_RATE = 1/3


config_file = open("repair.conf", "r")
configs = config_file.readlines()
for c in configs:
    if c != "\n" and not c.startswith("#"):
        c = c.strip().split("=")
        param, val = c[0].lower(), c[1]
        if param == "src_file":
            SRC_FILE = val
            print("Using SRC_FILE = %s" % SRC_FILE)
        elif param == "test_bench":
            TEST_BENCH = val
            print("Using TEST_BENCH = %s" % TEST_BENCH)
        elif param == "oracle":
            ORACLE = val
            print("Using ORACLE = %s" % ORACLE)
        elif param == "gens":
            GENS = int(val)
            print("Using GENS = %d" % GENS)
        elif param == "popsize":
            POPSIZE = int(val)
            print("Using POPSIZE = %d" % POPSIZE)
        elif param == "deletion_rate":
            DELETION_RATE = float(val)
            print("Using DELETION_RATE = %f" % DELETION_RATE)
        elif param == "insertion_rate":
            INSERTION_RATE = float(val)
            print("Using INSERTION_RATE = %f" % INSERTION_RATE)
        elif param == "replacement_rate":
            REPLACEMENT_RATE = float(val)
            print("Using REPLACEMENT_RATE = %f" % REPLACEMENT_RATE)
        elif param == "restarts":
            RESTARTS = int(val)
            print("Using RESTARTS = %d" % RESTARTS)
        elif param == "fault_loc":          
            if val.lower() == "true": FAULT_LOC = True
            if val.lower() == "false": FAULT_LOC = False
            print("Using FAULT_LOC = %s" % FAULT_LOC) 
        elif param == "control_flow":          
            if val.lower() == "true": CONTROL_FLOW = True
            if val.lower() == "false": CONTROL_FLOW = False
            print("Using CONTROL_FLOW = %s" % CONTROL_FLOW) 
        elif param == "limit_transitive_dependency_set":          
            if val.lower() == "true": LIMIT_TRANSITIVE_DEPENDENCY_SET = True
            if val.lower() == "false": LIMIT_TRANSITIVE_DEPENDENCY_SET = False
            print("Using LIMIT_TRANSITIVE_DEPENDENCY_SET = %s" % LIMIT_TRANSITIVE_DEPENDENCY_SET) 
        elif param == "dependency_set_max":
            DEPENDENCY_SET_MAX = int(val)
            print("Using DEPENDENCY_SET_MAX = %d" % DEPENDENCY_SET_MAX)
        else:
            print("ERROR: Invalid parameter: %s" % param)
            exit(1)
config_file.close()

if not SRC_FILE:
    print("ERROR: SRC_FILE not specified. Please check the configuration file.")
    exit(1)
elif not TEST_BENCH:
    print("ERROR: TEST_BENCH not specified. Please check the configuration file.")
    exit(1)
elif not ORACLE:
    print("ERROR: ORACLE not specified. Please check the configuration file.")
    exit(1)

if REPLACEMENT_RATE + INSERTION_RATE + DELETION_RATE != 1.0:
    print("ERROR: The mutation operator rates should add up to 1.")
    exit(1)

class MutationOp(ASTCodeGenerator):

    def __init__(self, popsize, fault_loc, control_flow):
        self.numbering = NodeNumbering()
        self.popsize = popsize
        self.fault_loc = fault_loc
        self.control_flow = control_flow
        # temporary variables used for storing data for the mutation operators
        self.fault_loc_set = set()
        self.new_vars_in_fault_loc = dict()
        self.wires_brought_in = dict()
        self.blacklist = set()
        self.tmp_node = None 
        self.deletable_nodes = []
        self.insertable_nodes = []
        self.replaceable_nodes = []
        self.node_class_to_replace = None
        self.stmt_nodes = []
        self.max_node_id = -1

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
            if after_id == ast.node_id:
                ast.statements.insert(0, copy.deepcopy(node))
            else:
                insert_point = -1
                for i in range(len(ast.statements)):
                    stmt = ast.statements[i]
                    if stmt and stmt.node_id == after_id:
                        insert_point = i + 1
                        break
                if insert_point != -1:
                    # print(ast.statements)
                    ast.statements.insert(insert_point, copy.deepcopy(node))
                    # print(ast.statements)
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
        # with fault localization, make sure that any node being deleted is also in DELETE_TARGETS 
        if self.fault_loc and len(self.fault_loc_set) > 0:
            if ast.node_id in self.fault_loc_set and ast.__class__.__name__ in DELETE_TARGETS:
                self.deletable_nodes.append(ast.node_id)
        else:
            if ast.__class__.__name__ in DELETE_TARGETS:
                self.deletable_nodes.append(ast.node_id)

        for c in ast.children():
            if c: self.get_deletable_nodes(c) 

    """
    Gets a list of all nodes that can be inserted into to a begin ... end block.
    """
    def get_insertable_nodes(self, ast):
        # with fault localization, make sure that any node being used is also in INSERT_TARGETS (to avoid inserting, e.g., overflow+1 into a block statement)
        if self.fault_loc and len(self.fault_loc_set) > 0: 
            if ast.node_id in self.fault_loc_set and ast.__class__.__name__ in INSERT_TARGETS:
                self.insertable_nodes.append(ast.node_id)
        else:        
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
    Control dependency analysis of the given program branch.
    """
    def analyze_program_branch(self, ast, cond, mismatch_set, uniq_headers):
        if ast:
            if ast.__class__.__name__ == "Identifier" and (ast.name in mismatch_set or ast.name in tuple(self.new_vars_in_fault_loc.values())):
                self.add_node_and_children_to_fault_loc(cond, mismatch_set, uniq_headers, ast)

            for c in ast.children():
                self.analyze_program_branch(c, cond, mismatch_set, uniq_headers)

    """
    Add node and its immediate children to the fault loc set.    
    """
    def add_node_and_children_to_fault_loc(self, ast, mismatch_set, uniq_headers, parent=None):
        if ast.__class__.__name__ == "Identifier" and ast.name in self.blacklist: return
        self.fault_loc_set.add(ast.node_id)
        if parent and parent.__class__.__name__ == "Identifier" and parent.name not in self.wires_brought_in: self.wires_brought_in[parent.name] = set()
        if ast.__class__.__name__ == "Identifier" and ast.name not in mismatch_set and ast.name not in uniq_headers and ast.name not in self.blacklist: 
            if not LIMIT_TRANSITIVE_DEPENDENCY_SET or len(self.wires_brought_in[parent.name]) < DEPENDENCY_SET_MAX:
                self.wires_brought_in[parent.name].add(ast.name)
                self.new_vars_in_fault_loc[ast.node_id] = ast.name
            else:
                self.blacklist.add(ast.name)
        for c in ast.children():
            if c:
                self.fault_loc_set.add(c.node_id) 
                # add all children identifiers to depedency set
                if c.__class__.__name__ == "Identifier" and c.name not in mismatch_set and c.name not in uniq_headers and c.name not in self.blacklist: 
                    if not LIMIT_TRANSITIVE_DEPENDENCY_SET or len(self.wires_brought_in[parent.name]) < DEPENDENCY_SET_MAX: 
                        self.wires_brought_in[parent.name].add(c.name)
                        self.new_vars_in_fault_loc[c.node_id] = c.name
                    else:
                        self.blacklist.add(c.name)

    """
    Given a set of output wires that mismatch with the oracle, get a list of node IDs that are potential fault localization targets.
    """
    def get_fault_loc_targets(self, ast, mismatch_set, uniq_headers, parent=None, include_all_subnodes=False):
        # data dependency analysis
        if ast.__class__.__name__ == "Identifier" and ast.name in self.blacklist: return
        if ast.__class__.__name__ in ["BlockingSubstitution", "NonblockingSubstitution", "Assign"]: # for assignment statements =, <=
            if ast.left and ast.left.var:
                if ast.left.var.__class__.__name__ == "Identifier" and ast.left.var.name in mismatch_set: # single assignment
                    include_all_subnodes = True
                    parent = ast.left.var
                    if parent and not parent.name in self.wires_brought_in: self.wires_brought_in[parent.name] = set()
                    self.add_node_and_children_to_fault_loc(ast, mismatch_set, uniq_headers, parent)
                elif ast.left.var.__class__.__name__ == "LConcat": # l-concat / multiple assignments
                    for v in ast.left.var.list: 
                        if v.name in mismatch_set:
                            if not v.name in self.wires_brought_in: self.wires_brought_in[v.name] = set()
                            include_all_subnodes = True
                            parent = v
                            self.add_node_and_children_to_fault_loc(ast, mismatch_set, uniq_headers, parent)
        
        # control dependency analysis        
        elif self.control_flow and ast.__class__.__name__ == "IfStatement":
            self.analyze_program_branch(ast.true_statement, ast.cond, mismatch_set, uniq_headers)
            self.analyze_program_branch(ast.false_statement, ast.cond, mismatch_set, uniq_headers)
        elif self.control_flow and ast.__class__.__name__ == "CaseStatement":
            for c in ast.caselist: 
                if c: self.analyze_program_branch(c.statement, ast.comp, mismatch_set, uniq_headers)
        elif self.control_flow and ast.__class__.__name__ == "ForStatement":
            # TODO: could improve efficiency by doing all of this in one function call instead of three; would need to add support for a list of conds
            if ast.pre: self.analyze_program_branch(ast.statement, ast.pre, mismatch_set, uniq_headers)
            if ast.cond: self.analyze_program_branch(ast.statement, ast.cond, mismatch_set, uniq_headers)
            if ast.post: self.analyze_program_branch(ast.statement, ast.post, mismatch_set, uniq_headers)


        if include_all_subnodes: # recurisvely ensure all children of a fault loc target are also included in the fault loc set
            self.fault_loc_set.add(ast.node_id)
            if ast.__class__.__name__ == "Identifier" and ast.name not in mismatch_set and ast.name not in uniq_headers and ast.name not in self.blacklist:
                if parent and parent.__class__.__name__ == "Identifier":
                    if not LIMIT_TRANSITIVE_DEPENDENCY_SET or len(self.wires_brought_in[parent.name]) < DEPENDENCY_SET_MAX: 
                        self.wires_brought_in[parent.name].add(ast.name)
                        self.new_vars_in_fault_loc[ast.node_id] = ast.name
                    else:
                        self.blacklist.add(ast.name)

        for c in ast.children():
            if c: self.get_fault_loc_targets(c, mismatch_set, uniq_headers, parent, include_all_subnodes)

        # TODO: for sdram_controller, control_flow + limit gives smaller fl set than no control_flow + limit. why? is this a bug?
    
    """
    The delete, insert, and replace operators to be called from outside the class.
    Note: node_id, with_id, and after_id would not be none if we are trying to regenerate AST from patch list, and would be none for a random mutation.
    """
    def delete(self, ast, patch_list, node_id=None):
        if node_id == None:
            self.get_deletable_nodes(ast) # get all nodes that can be deleted without breaking the AST / syntax
            if len(self.deletable_nodes) == 0: # if no nodes can be deleted, return without attepmting delete
                print("Delete operation not possible. Returning with no-op.")
                return patch_list, ast
            node_id = random.choice(self.deletable_nodes) # choose a random node_id to delete
            print("Deleting node with id %s\n" % node_id)

        self.delete_node(ast, node_id) # delete the node corresponding to node_id
        self.numbering.renumber(ast) # renumber nodes
        self.max_node_id = self.numbering.c # reset max_node_id
        self.numbering.c = -1
        self.deletable_nodes = [] # reset deletable nodes for the next delete operation

        child_patchlist = copy.deepcopy(patch_list)
        child_patchlist.append("delete(%s)" % node_id) # update patch list

        return child_patchlist, ast
    
    def insert(self, ast, patch_list, node_id=None, after_id=None):
        if node_id == None and after_id == None:
            self.get_insertable_nodes(ast) # get all nodes with a type that is suited to insertion in block statements -> src
            self.get_nodes_in_block_stmt(ast) # get all nodes within a block statement -> dest
            if len(self.insertable_nodes) == 0 or len(self.stmt_nodes) == 0: # if no insertable nodes exist, exit gracefully
                print("Insert operation not possible. Returning with no-op.")
                return patch_list, ast
            after_id = random.choice(self.stmt_nodes) # choose a random src and dest
            node_id = random.choice(self.insertable_nodes)
            print("Inserting node with id %s after node with id %s\n" % (node_id, after_id))
        self.get_node_from_ast(ast, node_id) # get the node associated with the src node id
        self.insert_stmt_node(ast, self.tmp_node, after_id) # perform the insertion
        self.numbering.renumber(ast) # renumber nodes
        self.max_node_id = self.numbering.c # reset max_node_id
        self.numbering.c = -1
        self.insertable_nodes = [] # reset the temporary variables
        self.tmp_node = None
        
        child_patchlist = copy.deepcopy(patch_list)
        child_patchlist.append("insert(%s,%s)" % (node_id, after_id)) # update patch list

        return child_patchlist, ast
    
    def replace(self, ast, patch_list, node_id=None, with_id=None):
        if node_id == None:
            if self.max_node_id == -1: # if max_id is not know yet, traverse the AST to find the number of nodes -- needed to pick a random id to replace
                self.numbering.renumber(ast)
                self.max_node_id = self.numbering.c
                self.numbering.c = -1 # reset the counter for numbering
            if self.fault_loc and len(self.fault_loc_set) > 0:
                node_id = random.choice(tuple(self.fault_loc_set)) # get a fault loc target if fault localization is being used
            else:            
                node_id = random.randint(0,self.max_node_id) # get random node id to replace
            print("Node to replace id: %s" % node_id)

        if with_id == None: 
            self.get_node_to_replace_class(ast, node_id) # get the class of the node associated with the random node id
            print(self.node_class_to_replace)
            print("Node to replace class: %s" % self.node_class_to_replace)
            if self.node_class_to_replace == None: # if the node does not exist (could have been a part of gen i but not i-1) -> TODO: is this still needed?
                return patch_list, ast
            self.get_replaceable_nodes_by_class(ast, self.node_class_to_replace) # get all valid nodes that have a class that could be substituted for the original node's class
            if len(self.replaceable_nodes) == 0: # if no replaceable nodes exist, exit gracefully
                print("Replace operation not possible. Returning with no-op.")
                return patch_list, ast
            print(self.replaceable_nodes)
            with_id = random.choice(self.replaceable_nodes) # get a random node id from the replaceable nodes
            print("Replacing node id %s with node id %s" % (node_id,with_id))

        self.get_node_from_ast(ast, with_id) # get the node associated with with_id
        self.replace_with_node(ast, node_id, self.tmp_node) # perform the replacement
        self.tmp_node = None # reset the temporary variables
        self.replaceable_nodes = []
        self.node_class_to_replace = None
        self.numbering.renumber(ast) # renumber nodes
        self.max_node_id = self.numbering.c # update max_node_id
        self.numbering.c = -1
        
        child_patchlist = copy.deepcopy(patch_list)
        child_patchlist.append("replace(%s,%s)" % (node_id, with_id)) # update patch list

        return child_patchlist, ast
    
    def ast_from_patchlist(self, ast, patch_list):
        for m in patch_list:
            operator = m.split('(')[0]
            operands = m.split('(')[1].replace(')','').split(',')
            if operator == "replace":
                _, ast = self.replace(ast, patch_list, int(operands[0]), int(operands[1]))
            elif operator == "insert":
                _, ast = self.insert(ast, patch_list, int(operands[0]), int(operands[1]))
            elif operator == "delete":
                _, ast = self.delete(ast, patch_list, int(operands[0]))
            else:
                print("Invalid operator in patch list: %s" % m)
        return ast

def tournament_selection(mutation_op, codegen, orig_ast, popn):
    # Choose 10 random candidates for parent selection
    pool = copy.deepcopy(popn)
    while len(pool) > 5:
        r = random.choice(pool)
        pool.remove(r)

    # generate ast from patchlist for each candidate, compute fitness for each candidate
    max_fitness = -1
    # max_fitness = math.inf
    best_parent_ast = orig_ast
    best_parent_patchlist = []

    for parent_patchlist in pool:
        parent_fitness = GENOME_FITNESS_CACHE[str(parent_patchlist)]

        if parent_fitness > max_fitness:
        # if parent_fitness < max_fitness:
            max_fitness = parent_fitness
            winner_patchlist = parent_patchlist
    
    winner_ast = copy.deepcopy(orig_ast)
    winner_ast = mutation_op.ast_from_patchlist(winner_ast, winner_patchlist)
    
    return copy.deepcopy(winner_patchlist), winner_ast

def calc_candidate_fitness(fileName):
    print("Running VCS simulation")
    #os.system("cat %s" % fileName)
    t_start = time.time()
    os.system("""source /etc/profile.d/modules.sh
	module load vcs/2017.12-SP2-1
	timeout 20 vcs -sverilog +vc -Mupdate -line -full64 sys_defs.vh %s %s -o simv -R""" % (TEST_BENCH, fileName))
    #process = subprocess.run("runvcs candidate.v " + TEST_BENCH, shell=True, executable='/usr/local/bin/interactive_zsh', timeout=20)
    t_finish = time.time()
    
    if not os.path.exists("output.txt"): 
        return 0, t_finish - t_start # if the code does not compile, return 0
        # return math.inf

    f = open(ORACLE, "r")
    oracle_lines = f.readlines()
    f.close()

    f = open("output.txt", "r")
    sim_lines = f.readlines()
    f.close()

    weighting = "static"
    f = open("weights.txt", "r")
    weights = f.readlines()
    f.close()

    ff, total_possible = fitness.calculate_fitness(oracle_lines, sim_lines, weights, weighting)
    normalized_ff = ff/total_possible
    if normalized_ff < 0: normalized_ff = 0
    print("FITNESS = %f" % normalized_ff)

    return normalized_ff, t_finish - t_start
    # return fitness_v2.calculate_badness(oracle_lines, sim_lines, weights, weighting)

def get_elite_parents(popn, pop_size):
    elite_size = int(5/100 * pop_size)
    elite = []
    for parent in popn:
        elite.append((parent, GENOME_FITNESS_CACHE[str(parent)]))
    elite.sort(key = lambda x: x[1])
    return elite[-elite_size:]
    # return elite[:-elite_size]

def strip_bits(bits):
    for i in range(len(bits)):
        bits[i] = bits[i].strip()
    return bits

def get_output_mismatch():
    f = open(ORACLE, "r")
    oracle = f.readlines()
    f.close()

    f = open("output.txt", "r")
    sim = f.readlines()
    f.close()

    diff_bits = []

    headers = strip_bits(oracle[0].split(","))

    if len(oracle) != len(sim): # if the output and oracle are not the same length, all output wires are defined to be mismatched
        diff_bits = headers

    for i in range(1, len(oracle)):
        clk = oracle[i].split(",")[0]
        tmp_oracle = strip_bits(oracle[i].split(",")[1:])
        tmp_sim = strip_bits(sim[i].split(",")[1:])
        
        for b in range(len(tmp_oracle)):
            if tmp_oracle[b] != tmp_sim[b]:
                diff_bits.append(headers[b+1]) # offset by 1 since clk is also a header and is not an actual output
   
    res = set()

    for i in range(len(diff_bits)):
        tmp = diff_bits[i]
        if "[" in tmp:      
            res.add(tmp.split("[")[0])
        else:
            res.add(tmp)

    uniq_headers = set()
    for i in range(len(headers)):
        tmp = headers[i]
        if "[" in tmp:      
            uniq_headers.add(tmp.split("[")[0])
        else:
            uniq_headers.add(tmp)

    return res, uniq_headers

def main():
    start_time = time.time()

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

    filelist = [SRC_FILE, TEST_BENCH]

    if options.showversion:
        showVersion()

    for f in filelist:
        if not os.path.exists(f): raise IOError("file not found: " + f)

    if len(filelist) == 0:
        showVersion()

    LOG = False

    for i in range(1, len(sys.argv)):
        cmd = sys.argv[i]
        if "log" in cmd.lower():
            val = cmd.split("=")[1]
            if val.lower() == "true": LOG = True
            elif val.lower() == "false": LOG = False
            print("Using LOG = %s" % LOG)

    codegen = ASTCodeGenerator()
    # parse the files (in filelist) to ASTs (PyVerilog ast)
    ast, directives = parse([SRC_FILE],
                            preprocess_include=options.include,
                            preprocess_define=options.define)

    ast.show()
    src_code = codegen.visit(ast)
    print(src_code)
    print("\n")

    print("\n\n")

    # Generate the bit-weights
    bashCmd = ["python3", "bit_weighting.py", SRC_FILE]
    process = subprocess.Popen(bashCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    # process = subprocess.run(bashCmd, capture_output=True, check=True)
    # print(stdout, stderr) # if there is a CalledProcessError, uncomment this to see the contents of stderr

    mutation_op = MutationOp(POPSIZE, FAULT_LOC, CONTROL_FLOW)

    # manually testing sdram_controller
       
    # seed_patchlist, seed_ast = mutation_op.insert(copy.deepcopy(ast), [], 53, 78)
    # seed_ast.show()
    # tmp1 = codegen.visit(seed_ast)
    # f = open("candidate.v", "w+")
    # f.write(tmp1)
    # f.close()
    # ff_1 = calc_candidate_fitness("candidate.v")
    # print(ff_1)
    # os.remove("candidate.v")

    # mismatch_set, uniq_headers = get_output_mismatch()
    # print(mismatch_set)

    # mutation_op.get_fault_loc_targets(seed_ast, mismatch_set, uniq_headers) # compute fault localization for the parent
    # print("Fault Localization:", str(mutation_op.fault_loc_set))
    # while len(mutation_op.new_vars_in_fault_loc) > 0:
    #     new_mismatch_set = set(mutation_op.new_vars_in_fault_loc.values())
    #     print("New vars in fault loc:", new_mismatch_set)
    #     mutation_op.new_vars_in_fault_loc = dict()
    #     mismatch_set = mismatch_set.union(new_mismatch_set)
    #     mutation_op.get_fault_loc_targets(seed_ast, mismatch_set, uniq_headers) # compute fault localization for the parent
    #     print("Fault Localization:", str(mutation_op.fault_loc_set))
    # new_mismatch_set = set(mutation_op.new_vars_in_fault_loc.values())
    # print("Final mismatch set:", mismatch_set)
    # print(len(mutation_op.fault_loc_set))
    # exit(1)
    

    # seed2_ast = mutation_op.ast_from_patchlist(copy.deepcopy(ast), seed_patchlist)
    # seed2_patchlist, seed2_ast = mutation_op.replace(seed2_ast, seed_patchlist, 83, 44)
    # seed2_ast.show()
    # tmp1 = codegen.visit(seed2_ast)
    # f = open("candidate.v", "w+")
    # f.write(tmp1)
    # f.close()
    # print(tmp1)
    # print(seed2_patchlist)
    # ff_1 = calc_candidate_fitness("candidate.v")
    # print(ff_1)
    # os.remove("candidate.v")
    # exit(1)

    # calculate fitness of the original buggy program
    orig_fitness, sim_time = calc_candidate_fitness(SRC_FILE)
    #orig_fitness = ff_1
    GENOME_FITNESS_CACHE[str([])] = orig_fitness
    #GENOME_FITNESS_CACHE[str(['insert(53,78)'])] = orig_fitness
    print("Original program fitness = %f" % orig_fitness)

    mismatch_set, uniq_headers = get_output_mismatch()
    print(mismatch_set)
    
    if os.path.exists("output.txt"): os.remove("output.txt")

    # create log file
    if LOG:
        time_now = datetime.today().strftime('%Y-%m-%d-%H:%M:%S')
        benchmark = SRC_FILE.split("/")[-2]
        log_base_dir = "repair_logs/" + benchmark
        if not os.path.exists(log_base_dir):
            os.mkdir(log_base_dir)
            print("dir created: "+ log_base_dir)
        log_file = open("%s/repair_%s.log" % (log_base_dir, time_now), "w+")
        log_file.write("SOURCE FILE:\n\t %s\n" % SRC_FILE)
        log_file.write("TEST BENCH:\n\t %s\n" % TEST_BENCH)
        log_file.write("ORACLE:\n\t %s\n" % ORACLE)
        log_file.write("PARAMETERS:\n")
        log_file.write("\tgens=%d\n" % GENS)
        log_file.write("\tpopsize=%d\n" % POPSIZE)
        log_file.write("\trestarts=%d\n" % RESTARTS)
        log_file.write("\tfault_loc=%s\n" % FAULT_LOC)
        log_file.write("\tcontrol_flow=%s\n" % CONTROL_FLOW)
        log_file.write("\tlimit_transitive_dependency_set=%s\n" % LIMIT_TRANSITIVE_DEPENDENCY_SET)
        log_file.write("\tdependency_set_max=%s\n\n" % DEPENDENCY_SET_MAX)
    
    best_patches = dict()

    for restart_attempt in range(RESTARTS):
        popn = []
        popn.append([])
        #popn.append(['insert(53,78)'])
    
        for i in range(GENS): # for each generation
            print("\nIN GENERATION %d OF ATTEMPT %d" % (i, restart_attempt))
            if LOG: log_file.write("IN GENERATION %d OF ATTEMPT %d\n" % (i, restart_attempt))

            time.sleep(1)
            _children = []

            if i > 0: 
                elite_parents = get_elite_parents(popn, POPSIZE)
                for parent in elite_parents:
                    _children.append(parent[0])
                    if LOG: log_file.write("\t%s --elitism--> %s\t\t%f\n" % (str(parent[0]), str(parent[0]), parent[1]))
            
            while len(_children) < POPSIZE:
                # time.sleep(2) # use this to slow down the processing for debugging purposes
                parent_patchlist, parent_ast = tournament_selection(mutation_op, codegen, ast, popn)

                if mutation_op.fault_loc:
                    tmp_mismatch_set = copy.deepcopy(mismatch_set)
                    mutation_op.get_fault_loc_targets(parent_ast, tmp_mismatch_set, uniq_headers) # compute fault localization for the parent
                    print("Initial Fault Localization:", str(mutation_op.fault_loc_set))
                    while len(mutation_op.new_vars_in_fault_loc) > 0:
                        new_mismatch_set = set(mutation_op.new_vars_in_fault_loc.values())
                        print("New vars in fault loc:", new_mismatch_set)
                        mutation_op.new_vars_in_fault_loc = dict()
                        tmp_mismatch_set = tmp_mismatch_set.union(new_mismatch_set)
                        mutation_op.get_fault_loc_targets(parent_ast, tmp_mismatch_set, uniq_headers)
                        print("Fault Localization:", str(mutation_op.fault_loc_set))
                    print("Final mismatch set:", tmp_mismatch_set)
                    print("Final Fault Localization:", str(mutation_op.fault_loc_set))
                    print(len(mutation_op.fault_loc_set))
                    print(mutation_op.blacklist)
                    # print(mutation_op.wires_brought_in)

                # exit(1)

                p = random.random()
                if p >= REPLACEMENT_RATE:
                    child_patchlist, child_ast = mutation_op.replace(parent_ast, parent_patchlist)
                    if LOG: log_file.write("\t%s --mutation--> %s\t\t" % (str(parent_patchlist), str(child_patchlist)))
                elif p >= DELETION_RATE:
                    child_patchlist, child_ast = mutation_op.delete(parent_ast, parent_patchlist)
                    if LOG: log_file.write("\t%s --mutation--> %s\t\t" % (str(parent_patchlist), str(child_patchlist)))
                else:
                    child_patchlist, child_ast = mutation_op.insert(parent_ast, parent_patchlist)
                    if LOG: log_file.write("\t%s --mutation--> %s\t\t" % (str(parent_patchlist), str(child_patchlist)))

                #child_ast.show()
                # rslt = codegen.visit(child_ast)
                # print(rslt)
                print()
                print(child_patchlist)
                
                # calculate child fitness
                if str(child_patchlist) in GENOME_FITNESS_CACHE:
                    child_fitness = GENOME_FITNESS_CACHE[str(child_patchlist)]
                    print(child_fitness)
                else:
                    f = open("candidate.v", "w+")
                    code = codegen.visit(child_ast)
                    f.write(code)
                    f.close()

                    child_fitness = -1
                    # re-parse the written candidate to check for syntax errors -> zero fitness if the candidate does not compile
                    try:
                        tmp_ast, directives = parse(["candidate.v"])
                    except ParseError:
                        child_fitness = 0
                        # child_fitness = math.inf
                    # if the child fitness was not 0, i.e. the parser did not throw syntax errors
                    if child_fitness == -1: 
                        
                        child_fitness, sim_time = calc_candidate_fitness("candidate.v")
                        if os.path.exists("output.txt"): os.remove("output.txt")

                    os.remove("candidate.v")
                    
                    GENOME_FITNESS_CACHE[str(child_patchlist)] = child_fitness
                    print(child_fitness)

                if LOG: log_file.write("%f\n" % child_fitness)
                print("\n\n#################\n\n")

                if child_fitness == 1.0:
                    print("######## REPAIR FOUND IN ATTEMPT %d ########" % restart_attempt)
                    print(code)
                    print(child_patchlist)
                    total_time = time.time() - start_time
                    print("TOTAL TIME TAKEN TO FIND REPAIR = %f" % total_time)
                    sys.exit(1)

                _children.append(child_patchlist)
                mutation_op.fault_loc_set = set() # reset the fault localization data structures for the next parent
                mutation_op.new_vars_in_fault_loc = dict()
                mutation_op.wires_brought_in = dict()
                mutation_op.blacklist = set()
            
            popn = copy.deepcopy(_children)

            for i in popn: print(i)
            print()
    
        best_patches[restart_attempt] = get_elite_parents(popn, POPSIZE)
    
    total_time = time.time() - start_time
    print("TOTAL TIME TAKEN = %f" % total_time)
    if LOG: log_file.write("\n\n\nTOTAL TIME TAKEN = %f\n\n" % total_time)

    if LOG: log_file.write("BEST PATCHES:\n")
    for attempt in best_patches:
        print("Attempt number %d" % attempt)
        if LOG: log_file.write("\tAttempt number %d:\n" % attempt)
        for candidate in best_patches[attempt]: 
            print(candidate)
            if LOG: log_file.write("\t\t%s\n" % str(candidate))
        print()

    if LOG: log_file.close()

if __name__ == '__main__':
    main()
