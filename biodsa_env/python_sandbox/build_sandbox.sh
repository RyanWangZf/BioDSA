#!/bin/bash

# Build Docker image
nohup docker build . -t biodsa-sandbox-py --no-cache &> build.log &