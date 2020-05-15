#!/bin/bash

# how to run this bash script: ./eval_candidates.sh <candidates_dir>
module load vcs/2017.12-SP2-1

candidatesDir=$1

DONE=0

date>start_time.txt

echo $candidatesDir

for filename in $candidatesDir/*.v; do 

    #cat "$filename"

    timeout 20 vcs -sverilog +vc -Mupdate -line -full64 first_counter/sys_defs.vh first_counter/first_counter_tb_t1.v "$filename"  -o simv -R 

done

    
date>end_time.txt

