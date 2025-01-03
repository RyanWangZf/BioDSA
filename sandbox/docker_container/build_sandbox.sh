#!/bin/bash

# Build Docker image
nohup docker build . -t combined-sandbox --no-cache &> build.log &