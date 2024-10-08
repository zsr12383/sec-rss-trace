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
    local action=$4

    echo "Building image for $service_path using buildx"

    if [ "$action" == "build" ]; then
        # 빌드만 수행
        docker buildx build --platform linux/amd64,linux/arm64 -f $service_path/$dockerfile -t $image .
    elif [ "$action" == "push" ]; then
        # 빌드 및 푸시 수행
        docker buildx build --platform linux/amd64,linux/arm64 -f $service_path/$dockerfile -t $image . --push
    else
        echo "Invalid action. Use 'build' or 'push'."
        exit 1
    fi

    if [ $? -eq 0 ]; then
        echo "Image $image built successfully."
        [ "$action" == "push" ] && echo "Image $image pushed successfully."
    else
        echo "Failed to build or push $image"
    fi
}

# 인자를 기반으로 서비스별 빌드 및 푸시 또는 전체 수행
if [ "$1" == "sc13" ]; then
    build_and_push "sc13" "Dockerfile" $SC13_IMAGE $2
elif [ "$1" == "8k" ]; then
    build_and_push "8k" "Dockerfile" $EIGHTK_IMAGE $2
elif [ "$1" == "yahoo" ]; then
    build_and_push "yahoo" "Dockerfile" $YAHOO_IMAGE $2
elif [ "$1" == "all" ]; then
    build_and_push "sc13" "Dockerfile" $SC13_IMAGE $2
    build_and_push "8k" "Dockerfile" $EIGHTK_IMAGE $2
    build_and_push "yahoo" "Dockerfile" $YAHOO_IMAGE $2
else
    echo "Usage: $0 {sc13|8k|yahoo|all} {build|push}"
fi
