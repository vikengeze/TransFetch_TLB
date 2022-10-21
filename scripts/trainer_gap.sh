#!/bin/bash

if [ $# -eq 1 ]
  then
  	version=$1
  else
    echo "no version given"
    exit 1
fi

gap_p='/home/users/vgezekel/trace_files/gap/*'

for file in $gap_p; do
	./run_train.sh $(basename $file) $version 'gap'
done