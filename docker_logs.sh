#!/bin/bash
docker logs $(docker container ls | grep "cambot:latest" | cut -d' ' -f1)
