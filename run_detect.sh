echo ----------------------------start detecting ------------------------------

for((integer = 0; integer <= 24; integer ++))
do
  foo1="python /kaggle/working/MM-BD/univ_bd.py --model_dir model$integer"
  $foo1
done

