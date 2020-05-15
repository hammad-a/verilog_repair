#!/bin/bash

# how to run this bash script: ./run.sh first_counter.v
module load vcs/2017.12-SP2-1
module load verilog
mkdir ./candidates
mkdir ./repair
mkdir ./infinite
#generate tokens
# $1: original verilog file. e.g. fsm_cd.v
python lex.py $1 > tokens_temp.txt

python gen.py > tokens.v
DONE=0
# make one replace edit to the source tokens and generate a candiate:
# replace the j_th token with the i_th token
# the resulting file is: candidate_i_j.v
NUM=`wc -l tokens.v | awk '{print $1}'`

date>date0.txt
for (( i=0; i<$NUM; i++))
#DEBUG: for (( i=5; i<6; i++))
do
   
    if [ "$DONE" -eq "0" ]; then
        for(( j=0; j<$NUM; j++))
        #DEBUG:for(( j=57; j<58; j++))
        do
            rm output.txt
            echo "Repairing: replace $j with $i..."
            python repair.py tokens.v $i $j
            # the resulting file is: candidate_i_j.v
            echo "Generated: ./candidates/candidate_$i\_$j.v"

            # MD5SUM create a checksum for the candidate
            echo "#######">>checksum_log.txt
            md5sum ./candidates/candidate_$i\_$j.v>>checksum_log.txt
            
            # call vcs to check if it passed, if yes, done; if not, keep trying.
            #timeout 20 SW_VCS=2015.09 vcs -sverilog +vc -Mupdate -line -full64 sys_defs.vh test_cd.v ./candidates/candidate_$i\_$j.v  -o simv -R | tee program.out
            
            # record the starting time of this run
            echo "start:">>checksum_log.txt
            date>>checksum_log.txt

            timeout 20 vcs -sverilog +vc -Mupdate -line -full64 sys_defs.vh first_counter_tb_t2.v ./candidates/candidate_$i\_$j.v  -o simv -R 

            if [ `echo $?` -eq 124 ]; then
                echo "candidate_$i\_$j.v: time out"
                echo "timeout" >> checksum_log.txt
                cp ./candidates/candidate_$i\_$j.v ./infinite/
                echo "Made a copy for candidate_$i\_$j.v ..."
            else
                #Compare with the current output with the output oracle
                #record the end time of this run
                echo "end:">>checksum_log.txt
                date>>checksum_log.txt
                if [ -e ./output.txt ]; then
                    if [ -z `diff ./output.txt ./output_oracle.txt` ]; then
                        echo "!!!!!!!!!!!!!!!"
                        echo "Repair FOUND: candidate_$i\_$j.v"
                        echo "valid repair">>checksum_log.txt
                        cp ./candidates/candidate_$i\_$j.v ./repair/
                    else
                        # can compile but not correct
                        echo "invalid repair">>checksum_log.txt
                    fi
                else
                    echo "Cannot compile: output.txt not found">>checksum_log.txt
                fi
            fi
        done
    else
        #break
        echo "dummy print"
    fi
done
    
date>date2.txt

