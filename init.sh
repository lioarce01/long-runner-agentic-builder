#!/bin/bash

# Auto-generated init script

echo '📦 Setting up Python backend...'
python -m venv .venv
source .venv/bin/activate || .venv\Scripts\activate
pip install -r requirements.txt

echo '✅ Development environment ready!'
echo 'Press Ctrl+C to stop all services'
wait