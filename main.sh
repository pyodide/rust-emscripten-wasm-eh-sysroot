#!/bin/bash
set -euo pipefail

if [ ! -d emsdk ]; then 
    git clone https://github.com/emscripten-core/emsdk.git --depth 1
fi
./emsdk/emsdk install $1
./emsdk/emsdk activate $1
source ./emsdk/emsdk_env.sh

# Don't tell Rust it's running in CI or it gets mad that:
# "`llvm.download-ci-llvm` cannot be set to `true` on CI. Use `if-unchanged` instead."
unset GITHUB_ACTIONS

python3 main.py $@
