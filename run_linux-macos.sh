#!/usr/bin/env bash

DIR="$PWD"
CMD="python3 batchGDL/main.py"

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e "tell application \"Terminal\" to do script \"cd '$DIR' && $CMD\""
    exit 0
else
    python3 app.py
fi