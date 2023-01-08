#!/bin/sh

set -eufo pipefail

cd $(dirname "$0")

python3 main.py "$@"