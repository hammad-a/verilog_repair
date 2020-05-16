from __future__ import absolute_import
from __future__ import print_function
import sys
import os

def main():

    if len(sys.argv) != 2:
        print("Usage: python parse_vcs_output.py <filename.txt>")
        sys.exit(1)
    if not sys.argv[1].endswith(".txt"):
        print("Error: Please make sure that the input file has a .txt extension")

    fName = sys.argv[1]

    inFile = open(fName, "r")
    outFile = open(fName.split(".txt")[0]+"_stripped.txt", "w+")

    lines = inFile.readlines()

    start = -1
    end = -1

    for i in range(len(lines)):
        if lines[i].strip().startswith("time,"): # get header for the simulation table
            start = i
        elif "V C S   S i m u l a t i o n   R e p o r t" in lines[i]: # get end for the rows in the simulation table
            end = i
    
    if start == -1 or end == -1:
        print("Simulation error: Could not finish simulation. See output file for details.")
        outFile.write("Simulation error: Could not finish simulation. See output file for details.\n")
        inFile.close()
        outFile.close()
        sys.exit(1)
    
    for i in range(start, end):
         outFile.write(lines[i])
        
    print("VCS output stripped: %s" % fName.split(".txt")[0]+"_stripped.txt")
    
    inFile.close()
    outFile.close()


if __name__ == '__main__':
    main()
