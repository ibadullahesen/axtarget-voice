from flask import Flask, request, send_file, render_template_string, jsonify
import os
import uuid
import wave
import numpy as np
from scipy.io import wavfile
import io
import tempfile

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

def create_demo_audio(text):
    """Demo audio yarat - TTS olmadan"""
    sample_rate = 22050
    duration = len(text) * 0.1  # Mətn uzunluğuna görə müddət
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Mətnə əsasən tezlik dəyişir
    base_freq = 440
    audio_data = 0.5 * np.sin(2 * np.pi * base_freq * t)
    
    # Söz sərhədləri üçün pauza əlavə et
    for i in range(0, len(audio_data), int(sample_rate * 0.1)):
        if i + int(sample_rate * 0.05) < len(audio_data):
            audio_data[i:i+int(sample_rate * 0.05)] = 0
    
    # 16-bit audio
    audio_data = (audio_data * 32767).astype(np.int16)
    
    return sample_rate, audio_data

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AxtarGet Voice - Audio Demo</title>
    <meta charset="utf-8">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-purple-900 to-blue-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/10 backdrop-blur-lg rounded-2xl p-6 max-w-md w-full shadow-xl border border-white/20">
        <h1 class="text-3xl font-black text-center bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent mb-2">
            Audio Demo
        </h1>
        <p class="text-gray-300 text-center text-sm mb-4">Səs emalı demo sistemi</p>
        
        <form method="post" class="space-y-4">
            <div>
                <label class="block text-green-300 font-bold mb-2">Mətn</label>
                <textarea name="text" rows="3" required placeholder="Bu mətn audio-ya çevriləcək..." 
                          class="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400"></textarea>
            </div>
            
            <button type="submit" class="w-full py-3 bg-gradient-to-r from-green-500 to-blue-600 text-white font-bold rounded-lg hover:scale-105 transition">
                🔊 Audio Yarat
            </button>
        </form>

        {% if audio_url %}
        <div class="mt-4 p-4 bg-green-600/20 border border-green-400 rounded-lg text-center">
            <p class="text-green-300 font-bold mb-2">Audio hazırdır!</p>
            <audio controls class="w-full mb-2">
                <source src="{{ audio_url }}" type="audio/wav">
            </audio>
            <a href="{{ audio_url }}" class="text-blue-300 underline">📥 Endir</a>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        
        if text:
            unique_id = str(uuid.uuid4())
            output_path = os.path.join(UPLOAD_FOLDER, f"audio_{unique_id}.wav")
            
            # Demo audio yarat
            sample_rate, audio_data = create_demo_audio(text)
            
            # WAV faylına yaz
            wavfile.write(output_path, sample_rate, audio_data)
            
            return render_template_string(HTML, audio_url=f"/download/{unique_id}")
    
    return render_template_string(HTML)

@app.route("/download/<file_id>")
def download(file_id):
    file_path = os.path.join(UPLOAD_FOLDER, f"audio_{file_id}.wav")
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name="audio.wav")
    return "Fayl tapılmadı", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
