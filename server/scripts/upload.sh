#!/usr/bin/env bash
#
# This script allows you to upload scan data from your local machine to the server

UPLOAD_SERVER_URL='http://localhost:8000'
LOCAL_DATA_DIR=$1

UPLOAD_FILE_SUFFIXES=('.mp4' '.depth.zlib' '.confidence.zlib' '.json' '.jsonl')
SCAN_ID=${LOCAL_DATA_DIR##*/}

for SUFFIX in ${UPLOAD_FILE_SUFFIXES[@]}; do
	FILE_NAME=${SCAN_ID}${SUFFIX}
	FILE_PATH=${LOCAL_DATA_DIR}/${FILE_NAME}
	CHECK_SUM=$(md5sum $FILE_PATH | awk '{print $1}')
	
	# Upload to server
	curl -v -X PUT -H "FILE_NAME: $FILE_NAME" --data-binary "@$FILE_PATH" -H "Content-Type: application/ipad_scanner_data" ${UPLOAD_SERVER_URL}/upload
	# Verify
	curl -v "${UPLOAD_SERVER_URL}/verify?filename=$FILE_NAME&checksum=$CHECK_SUM"
	
	done
