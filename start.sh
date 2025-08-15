#!/bin/bash

# MySQL Database Transfer Tool - Startup Script
# Works on Linux, macOS, and other Unix-like systems

echo "MySQL Database Transfer Tool"
echo "=========================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.7+ and try again"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
MIN_VERSION="3.7"

if [[ $(echo "$PYTHON_VERSION $MIN_VERSION" | awk '{print ($1 < $2)}') == 1 ]]; then
    echo "ERROR: Python $PYTHON_VERSION found, but Python $MIN_VERSION or higher is required"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

# Install dependencies if needed
if [ ! -f "venv/lib/python*/site-packages/flask/__init__.py" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

# Check if config file exists
if [ ! -f "config.json" ]; then
    echo
    echo "WARNING: config.json not found!"
    echo "Please copy config.json.template to config.json and update with your database settings"
    echo
    read -p "Press Enter to continue..."
fi

# Start the application
echo "Starting MySQL Database Transfer Tool..."
echo "Open your browser and navigate to: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo

python app.py
