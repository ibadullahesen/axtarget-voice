#!/bin/bash
set -e

echo "=== Pip upgrade edilir ==="
pip install --upgrade pip

echo "=== TTS və digər kitabxanalar yüklənir ==="
pip install -r requirements.txt

echo "=== Model yoxlanılır ==="
python -c "
print('Sistem yoxlanılır...')
try:
    from TTS.api import TTS
    print('✅ TTS uğurla import edildi')
    print('ℹ️ Model ilk istifadədə avtomatik yüklənəcək')
except Exception as e:
    print(f'❌ Xəta: {e}')
"

echo "=== Build tamamlandı ==="
