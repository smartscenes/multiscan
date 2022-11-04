#!/usr/bin/env bash
#
# Converts mp4 raw video streams to compressed mp4

OUT_WIDTH=320
VERBOSE=false
SKIPDONE=false
FFMPEG=${FFMPEG:-ffmpeg}

function run {
    for mp4 in `find "${DIR}" -name "*.mp4"`; do
        preview=${mp4/\.mp4/_preview\.mp4}
        if [[ ("$SKIPDONE" = true) && (-s ${preview}) ]]; then
            # Skip this
            continue
        fi
        if [[ ${mp4} == *"preview"* ]]; then
            continue
        fi
        if [ "$VERBOSE" = true ]; then
            echo "Create mp4: ${mp4} to ${preview}"
        fi
        "${FFMPEG}" -y -i "${mp4}" -vf "scale=${OUT_WIDTH}:-1" -vcodec libx264 -pix_fmt yuv420p -r 25 -movflags faststart "${preview}"
    done
    echo "Done."
}

while true; do
    case "$1" in
        -h)
            echo "Usage: $0 [-h] [-v] [--skip-done] <dir> [width]"
            echo "Converts.mp4 raw stream to lower bitrate .mp4"
            echo "[-h] prints this help message and quits"
            echo "[-v] verbose mode"
            echo "[--skip-done] skips images with existing thumbnails"
            echo "[width] is optional and must be width in pixels"
            echo "All parameters are positional"
            exit 1
            ;;
        -v)
            VERBOSE=true
            shift
            ;;
        --skip-done)
            SKIPDONE=true
            shift
            ;;
        *)
            DIR="$1"
            shift
            break
    esac
done

if [ -z $DIR ]
then
   echo "Please specify input directory"
   exit 1
fi

if [ -n "$1" ]; then
    OUT_WIDTH="$1"
fi

run
