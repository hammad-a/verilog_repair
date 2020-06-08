<ins>For the fitness function:</ins>
1. Modify the test bench to produce an output file similar to the format below:
    time,out_1,out_2,out_3,out_4
    5,x,x,x,x
    10,1,0,0,0
    ...
2. Make sure that the variable name headers in the output file match the variable names in the .v file. This is important for the parsing functionality of script bit_weighting.py script.
3. Produce the weights.txt file by running "python3 bit_weighting.py <verilog_file.v>".
4. Produce the fitness value by running "python3 fitness.py <oracle.txt> <output.txt> <weights.txt>". Note that the weights.txt file is optional; if it is omitted, a default bit weight of 1 is assigned to all output bits.
