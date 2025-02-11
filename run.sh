#!/bin/bash

# Ensure output directory exists for standalone mode
mkdir -p output

# Build Docker image
docker build -t cfa-app-trade-monitor .

# Run Unit Tests inside Docker
# echo "Running unit tests..."
# docker run --rm cfa-app-trade-monitor python -m unittest discover -v || { echo "Unit tests failed! Exiting."; exit 1; }

# Run the container with volume mounting for output
docker run --rm -e RUNNING_IN_DOCKER=1 -v $(pwd)/output:/app/output cfa-app-trade-monitor

# Move the generated report to output if it exists
if [ -f output/suspicious_trades_report.csv ]; then
    echo "Report successfully generated in output/"
else
    echo "Error: Report file not found!"
    exit 1
fi
