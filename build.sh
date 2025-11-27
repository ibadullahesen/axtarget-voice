#!/bin/bash
set -e

echo "=== Pip upgrade edilir ==="
pip install --upgrade pip

echo "=== Kitabxanalar yüklənir ==="
pip install -r requirements.txt

echo "=== Model yoxlanılır (LAZY loading) ==="
# Modeli deploy zamanı YOX, ilk istifadədə yüklə
python -c "
print('TTS kitabxanası yoxlanılır...')
from TTS.api import TTS
print('TTS uğurla import edildi - model lazy loading ilə işləyəcək')
"

echo "=== Build tamamlandı ==="
