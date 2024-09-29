#!/bin/bash

# 이미지 태그
SC13_IMAGE="zsr12383/sc13-trace:latest"
EIGHTK_IMAGE="zsr12383/8k:latest"
YAHOO_IMAGE="zsr12383/yahoo-bot:latest"

# 빌드 및 푸시 함수 (buildx 사용)
build_and_push() {
    local service_path=$1
    local dockerfile=$2
    local image=$3

    echo "Building image for $service_path using buildx"

    # buildx를 사용하여 빌드 및 푸시
#    docker buildx build --platform linux/amd64,linux/arm64 -f $service_path/$dockerfile -t $image $service_path --push
    docker buildx build --platform linux/amd64,linux/arm64 -f $service_path/$dockerfile -t $image . --push

    if [ $? -eq 0 ]; then
        echo "Image $image built and pushed successfully."
    else
        echo "Failed to build and push $image"
    fi
}

# 인자를 기반으로 서비스별 빌드 및 푸시 또는 전체 수행
if [ "$1" == "sc13" ]; then
    build_and_push "sc13" "Dockerfile" $SC13_IMAGE
elif [ "$1" == "8k" ]; then
    build_and_push "8k" "Dockerfile" $EIGHTK_IMAGE
elif [ "$1" == "yahoo" ]; then
    build_and_push "yahoo" "Dockerfile" $YAHOO_IMAGE
elif [ "$1" == "all" ]; then
    build_and_push "sc13" "Dockerfile" $SC13_IMAGE
    build_and_push "8k" "Dockerfile" $EIGHTK_IMAGE
    build_and_push "yahoo" "Dockerfile" $YAHOO_IMAGE
else
    echo "Usage: $0 {sc13|8k|yahoo|all}"
fi
