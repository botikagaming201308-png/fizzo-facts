#!/usr/bin/env bash
# Downloads the free Kokoro voice model (~350 MB) into ~/kokoro if it is missing.
set -e
mkdir -p ~/kokoro
cd ~/kokoro
[ -s kokoro.onnx ] || curl -sSL -o kokoro.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -s voices.bin ] || curl -sSL -o voices.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
python3 -c "import onnxruntime, numpy, PIL" && which ffmpeg >/dev/null && echo "setup ok"
