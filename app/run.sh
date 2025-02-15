running_pid=$(pgrep -f "run.py" | grep -v $$)
kill running_pid
nohup python run.py > run.out 2>&1 &