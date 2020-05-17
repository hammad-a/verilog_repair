#!/bin/bash

# how to run this bash script: ./eval_candidates.sh <candidates_dir> <testbench.v>
module load vcs/2017.12-SP2-1

candidatesDir=$1
tb=$2

DONE=0

date>start_time.txt

echo $candidatesDir

timeout 20 vcs -sverilog +vc -Mupdate -line -full64 first_counter/sys_defs.vh $tb first_counter/first_counter.v  -o simv -R | tee output_oracle.txt
python strip_vcs_output.py output_oracle.txt

rm repairs.txt
touch repairs.txt

for filename in $candidatesDir/*.v; do 

    #cat "$filename"
    rm output.txt
    rm output_stripped.txt

    timeout 20 vcs -sverilog +vc -Mupdate -line -full64 first_counter/sys_defs.vh $tb "$filename"  -o simv -R | tee output.txt 
    python strip_vcs_output.py output.txt
    
    cmp output_stripped.txt output_oracle_stripped.txt

    if [ $? -eq 0  ]; then
	echo "REPAIR FOUND!!!!!!!"
	echo $filename >> repairs.txt
    fi  

done

    
date>end_time.txt

