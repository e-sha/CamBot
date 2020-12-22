#!/bin/bash

set -x -e

script_dir=$(realpath $(dirname $0))
docker build $script_dir -t cambot:latest
