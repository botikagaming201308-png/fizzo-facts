#!/usr/bin/env bash
# Downloads the free Kokoro voice model (~350 MB) into ~/kokoro if it is missing.
set -e
mkdir -p ~/kokoro
cd ~/kokoro
BASE=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
# Fetch with retries; never keep an HTML error page (e.g. a 504) as the model file.
get() { # name url minbytes
  if [ -f "$1" ] && [ "$(stat -c%s "$1")" -ge "$3" ]; then return 0; fi
  for i in 1 2 3 4 5 6; do
    rm -f "$1.part"
    curl -fsSL --retry 3 --retry-delay 5 -o "$1.part" "$2" && [ "$(stat -c%s "$1.part")" -ge "$3" ] && mv "$1.part" "$1" && return 0
    echo "download of $1 failed (try $i), retrying..." >&2; sleep 15
  done
  rm -f "$1.part"; echo "ERROR: could not download $1" >&2; exit 1
}
get kokoro.onnx $BASE/kokoro-v1.0.onnx 300000000
get voices.bin $BASE/voices-v1.0.bin 20000000
python3 -c "import numpy as np; v=np.load('voices.bin'); assert 'am_puck' in v and 'bm_george' in v"
python3 -c "import onnxruntime, numpy, PIL" && which ffmpeg >/dev/null && echo "setup ok"
