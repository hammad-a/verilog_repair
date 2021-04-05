source /etc/profile.d/modules.sh
module load vcs/2017.12-SP2-1

cur_dir=`pwd`

cd $3

echo $1 $2
sed "s/$1/$2/g" vcs_sim_command > vcs_sim_command_buggy

cat vcs_sim_command_buggy
`cat vcs_sim_command_buggy`

rm vcs_sim_command_buggy

cp output_first_counter_tb_t3.txt $cur_dir/output_first_counter_tb_t3.txt
rm output_first_counter_tb_t3.txt

cd $cur_dir

