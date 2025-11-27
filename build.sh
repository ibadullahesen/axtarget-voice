#!/bin/bash
set -e

echo "=== Pip upgrade edilir ==="
pip install --upgrade pip

echo "=== Kitabxanalar yüklənir ==="
pip install -r requirements.txt

echo "=== Scipy və digər audio kitabxanaları yüklənir ==="
pip install scipy

echo "=== Build tamamlandı ==="
