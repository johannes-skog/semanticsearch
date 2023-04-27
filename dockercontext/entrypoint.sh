#!/usr/bin/bash
screen -S notebook -dm bash -c "jupyter notebook --ip 0.0.0.0 --allow-root --port 8085"

sleep infinity