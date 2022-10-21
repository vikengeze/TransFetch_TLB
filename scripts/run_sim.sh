#!/bin/bash

if [ "$#" -ne 3 ]; then
    echo "Illegal number of parameters"
    exit 1
fi

trace=$1
VERSION=$2
folder=$3

cd ./ChampSim

ROOT="../"
ChampSimTrace_ROOT="/various/dstyliar/ML-DPC/ChampSimTraces/"$folder"/"
OUTPUT_ROOT="../res"
app=${ChampSimTrace_ROOT}${trace}

OUTPUT_PATH=$OUTPUT_ROOT/$VERSION/sim
Gen_reports_path=$OUTPUT_ROOT/$VERSION/sim/reports
PrefFile_ROOT=$OUTPUT_ROOT/$VERSION/train
Gen_eval_path=$OUTPUT_PATH

mkdir -p $OUTPUT_PATH
mkdir -p $Gen_reports_path


WARM=51
SIM=50

echo "Starting simming for trace file "$app

./run_champsim.sh from_file-bimodal-no-no-no-lru-1core $WARM $SIM $app nn $VERSION

#./ml_prefetch_sim.py eval --results-dir $Gen_reports_path --output-file $Gen_eval_path/eval.csv

echo "Done for "$app
