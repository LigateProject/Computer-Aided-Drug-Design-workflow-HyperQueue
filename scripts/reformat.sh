#!/bin/bash

set -e

cd `dirname $0`/..

# Format Python code
ruff format

# Lint Python code
ruff check
