#!/bin/bash
set -euo pipefail

if [ ! -d emsdk ]; then 
    git clone https://github.com/emscripten-core/emsdk.git --depth 1
fi
./emsdk/emsdk install $1
./emsdk/emsdk activate $1
source ./emsdk/emsdk_env.sh
python3 main.py $@
