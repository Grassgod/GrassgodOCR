git pull
PIDS=$(ps aux | grep 'run.py' | awk '{print $2}')
echo "Killing PIDs: $PIDS"
kill $PIDS
nohup python run.py > run.out 2>&1 &