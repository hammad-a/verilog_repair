cur_dir=`pwd`

cd $3

echo $1 $2
sed "s/$1/$2/g" vcs_sim_command > vcs_sim_command_buggy

cat vcs_sim_command_buggy
. vcs_sim_command_buggy

rm vcs_sim_command_buggy

cp output_mux_4_1_tb.txt $cur_dir/output_mux_4_1_tb.txt
rm output_mux_4_1_tb.txt

cd $cur_dir

