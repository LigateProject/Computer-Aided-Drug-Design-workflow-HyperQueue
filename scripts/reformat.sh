#!/bin/bash

set -e

cd `dirname $0`/..

# Format Python code
isort --profile black ligate scripts tests
black ligate scripts tests

# Lint Python code
flake8 ligate scripts tests
