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

    line = inFile.readline()

    # get the header for the simulation table
    while not line.strip().startswith("time"):
        line = inFile.readline()
    print(line)
    outFile.write(line)

    # get the rows in the simulation table
    for line in inFile:
        if "V C S   S i m u l a t i o n   R e p o r t" in line:
            break
        print(line, end="")
        outFile.write(line)
    
    inFile.close()
    outFile.close()


if __name__ == '__main__':
    main()
