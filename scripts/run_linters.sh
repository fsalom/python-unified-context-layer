#!/bin/bash
FOLDER=$1

black -S ${FOLDER}
isort ${FOLDER}
