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
