#!/bin/bash
set -e

pip install --upgrade pip
pip install -r requirements.txt

# Əsas modeli əvvəlcədən endiririk ki, deploy zamanı timeout olmasın
python -c "
from TTS.api import TTS
print('Model endirilir...')
TTS('tts_models/multilingual/multi-dataset/xtts_v2', gpu=False)
print('Model hazır!')
"
