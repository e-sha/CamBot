#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <camera_id> <token>"
    exit -1
fi

set -x -e

CAM_ID=$1
TOKEN=$2

script_path=$(realpath $(dirname $0))
config_dir_path=$(mktemp -d)
config_file=${config_dir_path}/config.json
log_path=${script_path}/logs

echo "{ \"token\": \"$TOKEN\", \"camera_id\": 0, \"test\": { \"enable\": false } }" >$config_file
docker run -d -v ${config_dir_path}:/options -v ${log_path}:/logs --device=/dev/video${CAM_ID}:/dev/video0 cambot:latest
