#!/bin/bash

echo "========================================"
echo " ScaleV x Mailketing - Lead Management"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 tidak ditemukan!"
    echo "Silakan install Python3 terlebih dahulu."
    exit 1
fi

echo "[1/3] Checking dependencies..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "[2/3] Activating virtual environment..."
source venv/bin/activate

echo "[3/3] Installing/Updating dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "========================================"
echo " Starting Application..."
echo "========================================"
echo ""
echo " URL: http://localhost:5000"
echo " Press CTRL+C to stop"
echo ""

python3 app.py
