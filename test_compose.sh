#!/bin/bash

COMPOSE_FILE="docker-compose.yml"

# 도커 컴포즈 인자에 따라 동작 수행
if [ "$1" == "up" ]; then
    echo "Starting Docker Compose services..."
    docker-compose -f $COMPOSE_FILE up -d
    docker-compose -f $COMPOSE_FILE ps
    echo "Services are up and running."
elif [ "$1" == "down" ]; then
    echo "Stopping Docker Compose services..."
    docker-compose -f $COMPOSE_FILE down
    echo "Services are stopped."
else
    echo "Usage: $0 {up|down}"
fi
