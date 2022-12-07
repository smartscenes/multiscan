#!/usr/bin/env bash
#
# Simple script to index scannet staged and checked

BIN=`dirname $0`

STAGGING_DIR='../staging'
POPULATE_URL=http://localhost:3030/scans/populate?replace=all
CSV_PATH=$STAGGING_DIR/multiscan.csv
JSON_PATH=$STAGGING_DIR/multiscan.all.json
#ANNS_DIR=${SCANNET_DIR}/annotations

function run {
  # Index
  $BIN/../index.py --all --nonrecursive -i $STAGGING_DIR -o $CSV_PATH
  $BIN/../index.py --all --nonrecursive --format json -i $STAGGING_DIR -o $JSON_PATH

  # $BIN/../index.py -i $SCANS_DIR/checked -o $SCANS_DIR/checked/multiscan.csv
  # $BIN/../index.py --format json -i $SCANS_DIR/checked -o $SCANS_DIR/checked/multiscan.all.json

  # If there is annotation stats, merge them in
  #ANN_STATS=${ANNS_DIR}/scannet.anns.stats.csv
  #if [ -f ${ANN_STATS} ]; then
  #  echo "Combining stats from ${ANN_STATS}"
  #  cp $SCANS_DIR/checked/multiscan.csv $SCANS_DIR/checked/multiscan.nostats.csv
  #  $BIN/combine_stats.py --format csv -i $SCANS_DIR/checked/multiscan.nostats.csv -i ${ANN_STATS} $SCANS_DIR/checked/multiscan.csv
  #  cp $SCANS_DIR/checked/multiscan.all.json $SCANS_DIR/checked/multiscan.all.nostats.json
  #  $BIN/combine_stats.py --format json -i $SCANS_DIR/checked/multiscan.all.nostats.json -i ${ANN_STATS} $SCANS_DIR/checked/multiscan.all.json
  #fi


  # Tell our webui about it
  curl "$POPULATE_URL"  -H 'Content-Type: application/json' --data-binary "@$JSON_PATH"
  # curl "$WEBUI/scans/populate?group=checked&replace=group"  -H 'Content-Type: application/json' --data-binary "@$SCANS_DIR/checked/multiscan.all.json"
}

while true; do
    case "$1" in
        -h)
            echo "Usage: $0 [-h] [-v] [--staging_dir] [--populate_url] [--csv] [--json]"
            echo "Index all scans in the staging folder"
            echo "[-h] prints this help message and quits"
            echo "[--staging_dir] path to staging folder"
            echo "[--populate_url] web ui populate all scans url"
            echo "[--csv] output indexed csv file path"
            echo "[--json] output indexed json file path"
            exit 1
            ;;
        --staging_dir)
            STAGGING_DIR="$2"
            shift
            shift
            ;;
        --populate_url)
            POPULATE_URL="$2"
            shift
            shift
            ;;
        --csv)
            CSV_PATH="$2"
            shift
            shift
            ;;
        --json)
            JSON_PATH="$2"
            shift
            shift
            ;;
        *)
            break
    esac
done
echo "STAGGING DIR  = ${STAGGING_DIR}"
echo "POPULATE URL  = ${POPULATE_URL}"
echo "CSV PATH      = ${CSV_PATH}"
echo "JSON PATH     = ${JSON_PATH}"

if [ -n "$1" ]; then
    tail -1 $1
fi

run
