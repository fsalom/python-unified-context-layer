#!/bin/bash

RUN git config --global credential.helper store

# gula-python-common
echo "https://x-token-auth:${COMMONS_ACCESS_TOKEN}@bitbucket.org" > ~/.git-credentials

# chat-ia-python
# echo "https://x-token-auth:${CHATBOT_ACCESS_TOKEN}@bitbucket.org" > ~/.git-credentials

# gula-python-notifications
# echo "https://x-token-auth:${FCM_ACCESS_TOKEN}@bitbucket.org" > ~/.git-credentials
