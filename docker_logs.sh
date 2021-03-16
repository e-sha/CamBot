#!/bin/bash
CONTAINER_NAME=$(docker container ls | grep "cambot:latest" | cut -d' ' -f1)
if [[ -z "$CONTAINER_NAME" ]]; then
    CONTAINER_NAME=$(docker container ls -a | grep "cambot:latest" | cut -d' ' -f1 | head -n1)
    if [[ -z "$CONTAINER_NAME" ]]; then
        echo "No container found"
        exit -1
    else
        echo "Stopped container $CONTAINER_NAME"
    fi
else
    echo "Running container $CONTAINER_NAME"
fi
docker logs $CONTAINER_NAME
