#!/bin/bash
FOLDER=$1
BRANCH=$2
YML=$3
COMMONS_ACCESS_TOKEN=$4
CHATBOT_ACCESS_TOKEN=$5
FCM_ACCESS_TOKEN=$6

git pull origin $BRANCH
docker compose -p $FOLDER -f ~/$FOLDER/.docker/$YML build --build-arg COMMONS_ACCESS_TOKEN=$COMMONS_ACCESS_TOKEN --build-arg CHATBOT_ACCESS_TOKEN=$CHATBOT_ACCESS_TOKEN --build-arg FCM_ACCESS_TOKEN=$FCM_ACCESS_TOKEN
docker compose -p $FOLDER -f ~/$FOLDER/.docker/$YML stop
docker compose -p $FOLDER -f ~/$FOLDER/.docker/$YML rm -f
docker compose -p $FOLDER -f ~/$FOLDER/.docker/$YML up -d --remove-orphans
docker system prune --force
