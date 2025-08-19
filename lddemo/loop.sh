#!/bin/bash

for i in {1..5}; do
    echo "Running iteration $i..."
    poetry run bedrock-example
    echo "Completed iteration $i"
    echo "---"
    sleep 2
    echo "Sleep for 10"
done