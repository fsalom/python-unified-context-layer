#!/bin/bash

trap ctrl_c INT

RUN=1

# set local env vars
source .docker/scripts/local.sh

# Run Django
. scripts/run_django.sh &

# Run FastAPI
. scripts/run_fastapi.sh &

# Trap 'ctrl+c' action and run kill command to ensure both servers are down
function ctrl_c() {
        make kill-servers
        RUN=0
}

# Infinite loop breaks after detecting 'ctrl+c' action
while [[ $RUN == 1 ]]; do
    :
done
