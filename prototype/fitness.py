import sys
import os

X_WEIGHT = 1
DEBUG = False

# remove '\n' or other white space from bitlist 
def strip_bits(bits):
    for i in range(len(bits)):
        bits[i] = bits[i].strip()
    return bits

def calculate_fitness(oracle, sim):
    if len(oracle) != len(sim): # TODO: change this to append the sim file to match oracle length with x-bits
        return 0

    fitness = 0
    total_possible = 0 
    for i in range(1, len(oracle)):
        clk = oracle[i].split(",")[0]
        tmp_oracle = strip_bits(oracle[i].split(",")[1:])
        tmp_sim = strip_bits(sim[i].split(",")[1:])
        
        # print("Clock cycle: %s" % clk)
        for b in range(len(tmp_oracle)):
            if (tmp_oracle[b], tmp_sim[b]) in (('0', '0'), ('1', '1')):
                fitness += 1
                total_possible += 1
            elif (tmp_oracle[b], tmp_sim[b]) == ('x', 'x'):
                fitness += X_WEIGHT * 1
                total_possible += 1
            elif (tmp_oracle[b], tmp_sim[b]) in (('0', '1'), ('1', '0')):
                if DEBUG: print("Mismatch in bit %s of clock cycle %s (at time %s)..." % (b, i, clk))
                fitness -= 1
                total_possible += 1
            elif (tmp_oracle[b], tmp_sim[b]) in (('0', 'x'), ('1', 'x'), ('x', '0'), ('x', '1')):
                if DEBUG: print("Mismatch in x-bit %s of clock cycle %s (at time %s)..." % (b, i, clk))
                fitness -= X_WEIGHT * 1
                total_possible += X_WEIGHT * 1
        # print("Fitness = %s out of a total of %s" % (fitness, total_possible))
    return fitness, total_possible

def main():
    if len(sys.argv) != 3:
        print("USAGE: python3 fitness.py <oracle.txt> <output.txt>")
        sys.exit(1)
    
    f = open(sys.argv[1], "r")
    oracle_lines = f.readlines()
    f.close()

    f = open(sys.argv[2], "r")
    sim_lines = f.readlines()
    f.close()

    fitness, total_possible = calculate_fitness(oracle_lines, sim_lines)
    ff = fitness/total_possible
    print(ff)
    

if __name__ == '__main__':
    main()