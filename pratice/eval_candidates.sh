#!/bin/bash

# how to run this bash script: ./eval_candidates.sh <candidates_dir>
module load vcs/2017.12-SP2-1

candidatesDir=$2

DONE=0

date>start_time.txt

for filename in $candidatesDir; do 

    cat "$filename"

    #timeout 20 vcs -sverilog +vc -Mupdate -line -full64 sys_defs.vh first_counter_tb_t2.v ./candidates/candidate_$i\_$j.v  -o simv -R 

done

    
date>end_time.txt

