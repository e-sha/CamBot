#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <camera_id> <token_path>"
fi

CAM_ID=$1
TOKEN_PATH=$2

config_dir_path=$(mktemp -d)
config_file=${config_dir_path}/config.json


echo "{ \"token\": \"$(cat $TOKEN_PATH)\", \"camera_id\": $CAM_ID }" >$config_file
docker run -v ${config_dir_path}:/options --device=/dev/video0:/dev/video0 cambot:latest

rm -rf ${config_dir_path}
