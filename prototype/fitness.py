import sys
import os

X_WEIGHT = 1
DEBUG = False

# remove '\n' or other white space from bitlist 
def strip_bits(bits):
    for i in range(len(bits)):
        bits[i] = bits[i].strip()
    return bits

# parse the weights file
def get_weights(weights_file, oracle):
    weights_by_varname = dict()
    weights_by_bit = dict()
    
    for line in weights_file:
        line = line.strip()
        tmp = line.split("=")
        weights_by_varname[tmp[0]] = float(tmp[1])
    
    bits = strip_bits(oracle[0].split(","))
    for i in range(1, len(bits)):
        varname = bits[i]
        if "[" in varname:
            varname = varname.split("[")[0]
        weights_by_bit[i] = weights_by_varname.get(varname)
    
    return weights_by_bit

def calculate_fitness(oracle, sim, weights_file):

    weights = None
    if weights_file:
        weights = get_weights(weights_file, oracle)
    print(weights)
    
    if len(oracle) != len(sim): # TODO: change this to append the sim file to match oracle length with x-bits
        # resize_sim(oracle, sim)
        return 0

    fitness = 0
    total_possible = 0 
    for i in range(1, len(oracle)):
        clk = oracle[i].split(",")[0]
        tmp_oracle = strip_bits(oracle[i].split(",")[1:])
        tmp_sim = strip_bits(sim[i].split(",")[1:])

        # cycle_weight = 1/(2**(i-1))
        cycle_weight = 1
        
        for b in range(len(tmp_oracle)):
            if weights:
                bit_weight = weights[b+1] # off-set by 1 since time not included in b
            else:
                bit_weight = 1

            if (tmp_oracle[b], tmp_sim[b]) in (('0', '0'), ('1', '1')):
                fitness += bit_weight * cycle_weight * 1
                total_possible += bit_weight * cycle_weight * 1
            elif (tmp_oracle[b], tmp_sim[b]) == ('x', 'x'):
                fitness += bit_weight * cycle_weight * X_WEIGHT * 1
                total_possible += bit_weight * cycle_weight * X_WEIGHT * 1
            elif (tmp_oracle[b], tmp_sim[b]) in (('0', '1'), ('1', '0')):
                if DEBUG: print("Mismatch in bit %s of clock cycle %s (at time %s)..." % (b, i, clk))
                fitness -= bit_weight * cycle_weight * 1
                total_possible += bit_weight * cycle_weight * 1
            elif (tmp_oracle[b], tmp_sim[b]) in (('0', 'x'), ('1', 'x'), ('x', '0'), ('x', '1')):
                if DEBUG: print("Mismatch in x-bit %s of clock cycle %s (at time %s)..." % (b, i, clk))
                fitness -= bit_weight * cycle_weight * X_WEIGHT * 1
                total_possible += bit_weight * cycle_weight * X_WEIGHT * 1

    return fitness, total_possible

def main():
    if len(sys.argv) != 3 and len(sys.argv) != 4:
        print("USAGE: python3 fitness.py <oracle.txt> <output.txt> [weights.txt]")
        sys.exit(1)

    f = open(sys.argv[1], "r")
    oracle_lines = f.readlines()
    f.close()

    f = open(sys.argv[2], "r")
    sim_lines = f.readlines()
    f.close()

    weights = None
    if len(sys.argv) == 4:
        f = open(sys.argv[3], "r")
        weights = f.readlines()
        f.close()
        
    fitness, total_possible = calculate_fitness(oracle_lines, sim_lines, weights)
    ff = fitness/total_possible
    if ff < 0: ff = 0
    print(ff)

if __name__ == '__main__':
    main()