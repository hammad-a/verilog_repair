#!/bin/bash

source /etc/profile.d/modules.sh
module load vcs/2017.12-SP2-1

PROG=$1
TESTBENCH=$2
NUM_INPUTS=$3
K=$4

rm all_fuzzed_outputs.txt
touch all_fuzzed_outputs.txt

for (( i=0; i<$K; i++ )) 
do
    rm fuzzed_input.txt
    touch fuzzed_input.txt
    for (( j=0; j<$NUM_INPUTS; j++ )) 
    do
        echo $(((RANDOM%2))) >> fuzzed_input.txt
    done

    timeout 20 vcs -sverilog +vc -Mupdate -line -full64 sys_defs.vh $TESTBENCH $PROG -o simv -R

    if [ -e ./fuzzed_output.txt ]; then
        tail -1 fuzzed_output.txt >> all_fuzzed_outputs.txt
    fi
done
