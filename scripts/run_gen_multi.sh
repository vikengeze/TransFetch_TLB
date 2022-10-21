#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Illegal number of parameters"
    exit 1
fi

trace=$1
VERSION=$2
folder=$3

ROOT="./"
LoadTrace_ROOT="/home/users/vgezekel/trace_files/"$folder"/"
OUTPUT_ROOT="./res"

Python_ROOT=$ROOT"/NNroot"

TRAIN=20
VAL=10
TEST=70
SKIP=1

TRAIN_WARM=$TRAIN
TRAIN_TOTAL=$(($TRAIN + $VAL)) 

TEST_WARM=$TRAIN_WARM
TEST_TOTAL=$(($TRAIN+$TEST)) 

echo "Starting generation for trace file "$trace

file_path=$LoadTrace_ROOT/${trace}
model_path=$OUTPUT_ROOT/$VERSION/train/$(cut -d "-" -f-1 <<< ${trace}).model.pth

python3 $Python_ROOT/generate.py  $file_path  $model_path $TEST_WARM $TEST_TOTAL $SKIP

echo "Done with file " $trace
