#!/bin/bash
FOLDER=$1
MINIMAL_COV=$2

pytest -q --cov="${FOLDER}" --cov-fail-under="${MINIMAL_COV}" --cov-report term-missing tests
