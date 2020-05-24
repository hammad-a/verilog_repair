#!/bin/bash

module load vcs/2017.12-SP2-1

rm -r ./repair_candidates
rm -r ./repair_fixes
rm -r ./infinite_runs

mkdir repair_fixes
mkdir infinite_runs

PROG=$1
TESTBENCH=$2

echo "Generating repair candidates through mutation:"
python3 prototype.py $PROG

if [ ! -f output_oracle.txt ]; then
    echo "Output oracle does not exist." 
    echo "Attempting to generate oracle. What is the directory of the bug-free .v file?"
    read dir
    echo "What is the name of the bug-free .v file?"
    read correct_prog
    echo timeout 20 vcs -sverilog +vc -Mupdate -line -full64 sys_defs.vh $TESTBENCH "$correct_prog"  -o simv -R
    timeout 20 vcs -sverilog +vc -Mupdate -line -full64 sys_defs.vh $TESTBENCH "$correct_prog"  -o simv -R
    echo mv "$dir"/output.txt output_oracle.txt
    mv "$dir"/output.txt output_oracle.txt
    if [ ! -f output_oracle.txt ]; then
        echo "Generation of oracle failed. Terminating."
        exit 1
    fi
fi

DONE=0

for filename in ./repair_candidates/*.v; do 

    cat "$filename"

    rm output.txt
    timeout 20 vcs -sverilog +vc -Mupdate -line -full64 sys_defs.vh $TESTBENCH "$filename"  -o simv -R

    if [ `echo $?` -eq 124 ]; then
        echo "$filename: Time out. Copying to ./infinite_runs/"
        cp $filename ./infinite_runs/
    else
        #Compare with the current output with the output oracle
        #record the end time of this run
        if [ -e ./output.txt ]; then
            cmp ./output.txt ./output_oracle.txt
            if [ $? -eq 0  ]; then
                echo "!!!!!!!!!!!!!!!"
                echo "Repair FOUND: $filename"
                cp "$filename" ./repair_fixes/
            else
                # can compile but not correct
                echo "$filename: Invalid repair."
            fi
        else
            echo "$filename: Cannot compile; output.txt not found"
        fi
    fi

done

echo "A total of `ls -1 ./repair_fixes | wc -l` repairs found. See ./repair_fixes for more details."
echo "A total of `ls -1 ./infinite_runs | wc -l` runs timed out. See ./infinite_runs for more details."
