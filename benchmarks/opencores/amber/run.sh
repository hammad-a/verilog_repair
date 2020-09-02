cur_dir=`pwd`

cd $3

sed "s/$1/$2/g" run_all.sh > run_tmp.sh

bash run_tmp.sh $1 $2 $3

rm run_tmp.sh

cp output.txt $cur_dir/output.txt
rm output.txt

cd $cur_dir
