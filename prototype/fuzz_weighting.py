import sys, os
import math

# remove '\n' or other white space from bitlist 
def strip_bits(bits):
    for i in range(len(bits)):
        bits[i] = bits[i].strip()
    return bits

def get_differing_degree(arr, b):
    zeros = 0
    ones = 0
    for i in range(len(arr)):
        if arr[i][b] == '1':
            ones += 1
        elif arr[i][b] == '0':
            zeros += 1
    zeros_frac = zeros/len(arr)
    ones_frac = ones/len(arr)
    if zeros_frac > ones_frac:
        return zeros_frac - ones_frac
    else:
        return ones_frac - zeros_frac

# TODO: change this to use entropy instead?
def get_weights(results):
    weights = dict()
    var_names = strip_bits(results[0].split(","))
    arr = []

    # generate 2d array
    for i in range(1,len(results)):
        tmp = strip_bits(results[i].split(","))[1:]
        arr.append(tmp)

    # find the bits that change on fuzzed inputs
    diff = set()
    for i in range(len(arr)-1):
        for j in range(len(arr[i])):
            if arr[i][j] != arr[i+1][j]:
                diff.add(j)
    
    # compute weights
    for b in range(1, len(var_names)):
        if b not in diff:
            weights[var_names[b]] = 1
        else:
            d = get_differing_degree(arr,b)
            print(d)
            weights[var_names[b]] = 2 * (1/2**d)
            # weights[var_names[b]] = 2 * (1/math.e**d)
    
    for i in arr:
        print(i)

    return weights

def main():
    if len(sys.argv) != 2:
        print("USAGE: python3 fuzz_weighting.py <fuzz_results.txt>")
        sys.exit(1)

    f = open(sys.argv[1], "r")
    results = f.readlines()
    f.close()

    weights = get_weights(results)
    print(weights)

    f = open("fuzz_weights.txt", 'w+')
    for var in weights:
        print("Each bit of %s should have a weight of %s." % (var, weights[var]))
        f.write("%s=%s\n" % (var, weights[var]))
    f.close()
        
if __name__ == '__main__':
    main()