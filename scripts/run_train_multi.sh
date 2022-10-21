#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Illegal number of parameters"
    echo $1 $2 $3 
    exit 1
fi

app=$1
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

echo "TRAIN/VAL/TEST/SKIP: "$TRAIN"/"$VAL"/"$TEST"/"$SKIP

mkdir -p $OUTPUT_ROOT
mkdir -p $OUTPUT_ROOT/$VERSION
mkdir -p $OUTPUT_ROOT/$VERSION/train


echo "Starting training for trace file "$app
file_path=$LoadTrace_ROOT/${app}
model_path=$OUTPUT_ROOT/$VERSION/train/$(cut -d "-" -f-1 <<< ${app}).model.pth
echo $model_path
python3 $Python_ROOT/train.py  $file_path  $model_path $TRAIN_WARM $TRAIN_TOTAL $SKIP
    
echo "done for app "$app
