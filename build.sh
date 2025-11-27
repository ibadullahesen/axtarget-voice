#!/bin/bash
set -e
pip install --upgrade pip
pip install -r requirements.txt
echo "Model endirilir... (biraz gözlə)"
python -c "from TTS.api import TTS; TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)"
