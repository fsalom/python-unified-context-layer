#!/bin/bash

# Run linters
source scripts/run_linters.sh .

# Run tests and check the coverage
source scripts/run_tests.sh domain 90
source scripts/run_tests.sh application 90
source scripts/run_tests.sh driven 90
source scripts/run_tests.sh driving 90


# Run pylint
source scripts/run_pylint.sh domain
source scripts/run_pylint.sh application
source scripts/run_pylint.sh driven
source scripts/run_pylint.sh driving