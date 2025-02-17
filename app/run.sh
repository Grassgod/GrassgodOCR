kill $(ps aux | grep run.py | awk -wv grep | awk '{print $2}')
nohup python run.py > run.out 2>&1 &