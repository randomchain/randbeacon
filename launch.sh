#!/bin/bash

SESSION=randbeacon

tmux -2 new-session -d -s $SESSION

# Setup a window for tailing log files
tmux new-window -t $SESSION:1 -n 'proxies'
tmux select-layout tiled
tmux split-window -h
tmux select-pane -t 0
tmux send-keys "./proxy stream tcp://*:3333 tcp://*:4444 tcp://*:3344" C-m
tmux split-window -v
tmux resize-pane -U 50
tmux send-keys "echo STREAM PROXY SNOOPER; pipenv run python3 snooper.py tcp://localhost:3344" C-m
tmux select-pane -t 2
tmux send-keys "./proxy forward tcp://*:5555 tcp://*:6666 tcp://*:5566" C-m
tmux split-window -v
tmux resize-pane -U 50
tmux send-keys "echo FORWARD PROXY SNOOPER; pipenv run python3 snooper.py tcp://localhost:5566" C-m

tmux new-window -t $SESSION:2 -n 'input_collectors'
tmux split-window -v
tmux select-pane -t 0
tmux send-keys "pipenv run python3 randbeacon/input_collection/internal.py --push-connect tcp://localhost:3333" C-m
tmux select-pane -t 1
tmux send-keys "pipenv run python3 randbeacon/input_collection/simple_http.py --push-connect tcp://localhost:3333" C-m
tmux split-window -v
tmux send-keys "pipenv run python3 randbeacon/input_collection/simple_tcp.py --push-connect tcp://localhost:3333" C-m
tmux select-layout even-horizontal

tmux new-window -t $SESSION:3 -n 'middle'
tmux split-window -v
tmux select-pane -t 0
tmux send-keys "pipenv run python3 randbeacon/input_processing/merkle.py --pull-type connect --pull-addr tcp://localhost:4444" C-m
tmux select-pane -t 1
tmux send-keys "pipenv run python3 randbeacon/computation/delay_sloth.py --pub-type connect --pub-addr tcp://localhost:5555" C-m

tmux new-window -t $SESSION:4 -n 'publishers'
tmux split-window -v
tmux select-pane -t 0
tmux send-keys "pipenv run python3 snooper.py tcp://localhost:6666" C-m
tmux select-pane -t 1
tmux send-keys "pipenv run python3 randbeacon/publishing/json_dump.py --sub-connect tcp://localhost:6666 --json-output -" C-m

# Attach to session
tmux -2 attach-session -t $SESSION
