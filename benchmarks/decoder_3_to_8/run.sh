source /etc/profile.d/modules.sh
module load vcs/2017.12-SP2-1

cur_dir=`pwd`

cd $3

echo $1 $2
sed "s/$1/$2/g" vcs_sim_command > vcs_sim_command_buggy

cat vcs_sim_command_buggy
`cat vcs_sim_command_buggy`

rm vcs_sim_command_buggy

cp output.txt $cur_dir/output.txt
rm output.txt

cd $cur_dir

