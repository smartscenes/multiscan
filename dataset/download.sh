#!/bin/bash

function download {
    echo "Downloading MultiScan dataset ${OUTPUT_DIR}..."

    wget https://spathi.cmpt.sfu.ca/projects/multiscan/public_release/scans.txt -nc -P $OUTPUT_DIR

    while read scan; do 
        wget https://spathi.cmpt.sfu.ca/projects/multiscan/public_release/$scan.zip -nc -P $OUTPUT_DIR
    done <$OUTPUT_DIR/scans.txt
}

while true; do
    case "$1" in
        -h)
            echo "Usage: $0 [-v] <output_dir>"
            echo "download multiscan dataset"
            echo "[-h] prints this help message and quits"
            echo "[-v] verbose mode"
            exit 1
            ;;
        -v)
            VERBOSE=true
            shift
            ;;
        *)
            OUTPUT_DIR="$1"
            shift
            break
    esac
done

if [ -z $OUTPUT_DIR ]
then
   echo "Please specify output directory"
   exit 1
fi

download
