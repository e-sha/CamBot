#!/bin/bash
docker container kill $(docker container ls | grep "cambot:latest" | cut -d' ' -f1)
