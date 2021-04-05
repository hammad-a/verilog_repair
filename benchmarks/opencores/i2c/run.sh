source /etc/profile.d/modules.sh
module load vcs/2017.12-SP2-1

cur_dir=`pwd`

cd $3

echo $1 $2
sed "s/$1/$2/g" vcs_sim_command > vcs_sim_command_buggy

cat vcs_sim_command_buggy
`cat vcs_sim_command_buggy`

rm vcs_sim_command_buggy

#<<<<<<< HEAD
cp output_tst_bench_top_t1.txt $cur_dir/output_tst_bench_top_t1.txt
rm output_tst_bench_top_t1.txt
#=======
#cp output.txt $cur_dir/output.txt
#rm output.txt
#>>>>>>> 89e14778f7436711d11453e02e968083808e48f3

cd $cur_dir

