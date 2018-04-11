#!/bin/bash

SESSION=randbeacon

tmux -2 new-session -d -s $SESSION

# Setup a window for tailing log files
tmux new-window -t $SESSION:1 -n 'randbeacon'
tmux split-window -h
tmux select-pane -t 0
tmux send-keys "pipenv run python3 randbeacon/input_processing/merkle.py" C-m
tmux select-pane -t 1
tmux send-keys "pipenv run python3 randbeacon/computation/delay_sloth.py" C-m
tmux split-window -v
tmux resize-pane -D 20
tmux send-keys "pipenv run python3 randbeacon/input_collection/internal.py" C-m
tmux select-pane -t 0
tmux split-window -v
tmux resize-pane -D 20
tmux send-keys "pipenv run python3 randbeacon/input_collection/simple_http.py" C-m

# Attach to session
tmux -2 attach-session -t $SESSION
