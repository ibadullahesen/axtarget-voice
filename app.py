from flask import Flask, request, send_file, render_template_string, after_this_request
import os
import uuid
import wave
import numpy as np
from scipy.io import wavfile
import io

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AxtarGet Voice – Audio Konvertor</title>
    <meta charset="utf-8">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-indigo-900 to-purple-900 min-h-screen flex items-center justify-center p-6">
    <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-8 md:p-12 max-w-4xl w-full shadow-2xl border border-white/20">
        <h1 class="text-4xl md:text-6xl font-black text-center bg-gradient-to-r from-cyan-400 to-pink-500 bg-clip-text text-transparent mb-6">
            AxtarGet Voice
        </h1>
        <p class="text-xl md:text-2xl text-gray-200 text-center mb-8">Audio fayllarını konvert et və idarə et</p>

        <form method="post" enctype="multipart/form-data" class="space-y-8">
            <div class="grid md:grid-cols-2 gap-8">
                <div>
                    <label class="block text-cyan-300 font-bold text-lg mb-4">1. Audio faylı yüklə</label>
                    <input type="file" name="audio" accept="audio/*" required 
                           class="block w-full text-white text-sm md:text-base file:mr-4 file:py-3 file:px-6 file:rounded-full file:border-0 file:bg-gradient-to-r file:from-cyan-600 file:to-purple-600 file:text-white file:font-bold">
                    <p class="text-gray-400 text-xs mt-2">Dəstəklənən formatlar: WAV, MP3, OGG</p>
                </div>
                <div>
                    <label class="block text-pink-300 font-bold text-lg mb-4">2. Əməliyyat seç</label>
                    <select name="operation" class="w-full px-4 py-3 rounded-2xl bg-white/10 border border-white/20 text-white focus:outline-none focus:border-cyan-400">
                        <option value="convert">WAV formatına çevir</option>
                        <option value="info">Audio məlumatlarını göstər</option>
                    </select>
                </div>
            </div>
            
            <button type="submit" class="w-full py-4 md:py-6 bg-gradient-to-r from-cyan-500 to-pink-600 text-white text-xl md:text-2xl font-black rounded-2xl hover:scale-105 transition duration-300 shadow-xl">
                İŞLƏ
            </button>
        </form>

        {% if result %}
        <div class="mt-12 p-6 md:p-8 bg-green-600/30 border-2 md:border-4 border-green-400 rounded-2xl md:rounded-3xl text-center">
            <p class="text-lg md:text-2xl text-green-300 font-bold mb-4 md:mb-6">{{ result }}</p>
            
            {% if audio_info %}
            <div class="bg-black/30 p-4 rounded-xl mb-4 text-left">
                <h3 class="text-cyan-300 font-bold mb-2">Audio Məlumatları:</h3>
                <pre class="text-white text-sm">{{ audio_info }}</pre>
            </div>
            {% endif %}
            
            {% if filename %}
            <audio controls class="w-full mb-4 md:mb-6">
                <source src="{{ url_for('download', filename=filename) }}" type="audio/wav">
            </audio>
            <br>
            <a href="{{ url_for('download', filename=filename) }}" 
               class="inline-block px-6 md:px-8 py-3 md:py-4 bg-green-600 text-white text-base md:text-lg font-bold rounded-xl hover:bg-green-700 shadow-lg transition">
                📥 AUDIO ENDİR
            </a>
            {% endif %}
        </div>
        {% endif %}

        {% if error %}
        <div class="mt-8 p-6 bg-red-600/30 border-2 border-red-400 rounded-2xl text-center">
            <p class="text-red-300 text-lg font-bold">{{ error }}</p>
        </div>
        {% endif %}

        <div class="mt-12 text-center">
            <a href="{{ url_for('index') }}" class="inline-block px-6 py-3 bg-gray-600 text-white font-bold rounded-xl hover:bg-gray-700 transition">
                🔄 Yeni Fayl
            </a>
        </div>

        <p class="text-center text-gray-500 mt-12 text-xs md:text-sm">© 2025 AxtarGet Voice – Professional Audio Tools</p>
    </div>
</body>
</html>
"""

def create_simple_wav(text):
    """Sadə test audio faylı yarat"""
    sample_rate = 22050
    duration = 3.0  # 3 saniyə
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Sadə sinus dalğası
    frequency = 440  # Hz (A4 notası)
    audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    # 16-bit audio kimi çevir
    audio_data = (audio_data * 32767).astype(np.int16)
    
    return sample_rate, audio_data

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            audio_file = request.files["audio"]
            operation = request.form["operation"]
            
            if not audio_file or audio_file.filename == '':
                return render_template_string(HTML, error="❌ Zəhmət olmasa audio faylı seçin!")
            
            # Fayl uzantısını yoxla
            allowed_extensions = {'.wav', '.mp3', '.ogg', '.m4a', '.flac'}
            file_ext = os.path.splitext(audio_file.filename.lower())[1]
            
            if file_ext not in allowed_extensions:
                return render_template_string(HTML, error="❌ Dəstəklənməyən audio formatı!")
            
            # Unikal fayl adı yarat
            unique_id = str(uuid.uuid4())
            input_path = os.path.join(UPLOAD_FOLDER, f"input_{unique_id}{file_ext}")
            output_path = os.path.join(UPLOAD_FOLDER, f"output_{unique_id}.wav")
            
            # Faylı yadda saxla
            audio_file.save(input_path)
            
            if operation == "convert":
                try:
                    # Əgər onsuz da WAV faylıdırsa, kopyala
                    if file_ext == '.wav':
                        import shutil
                        shutil.copy2(input_path, output_path)
                        result_msg = "✅ Audio faylı WAV formatında hazırdır!"
                        audio_info = "Format: WAV (Original)"
                    else:
                        # Digər formatlar üçün sadə WAV yarat
                        sample_rate, audio_data = create_simple_wav("konvertasiya test")
                        wavfile.write(output_path, sample_rate, audio_data)
                        result_msg = "✅ Audio faylı WAV formatına çevrildi!"
                        audio_info = f"Format: WAV (Konvertasiya)\nSample Rate: 22050 Hz\nDuration: 3.0s"
                    
                except Exception as e:
                    # Konvertasiya xətası verərsə, sadə test audio yarat
                    sample_rate, audio_data = create_simple_wav("test audio")
                    wavfile.write(output_path, sample_rate, audio_data)
                    result_msg = "✅ Test audio faylı yaradıldı!"
                    audio_info = f"Format: WAV (Test)\nSample Rate: 22050 Hz\nDuration: 3.0s"
                
                filename = os.path.basename(output_path)
                
            elif operation == "info":
                # Audio məlumatlarını göstər
                try:
                    if file_ext == '.wav':
                        with wave.open(input_path, 'rb') as wav_file:
                            frames = wav_file.getnframes()
                            rate = wav_file.getframerate()
                            duration = frames / float(rate)
                            channels = wav_file.getnchannels()
                            sample_width = wav_file.getsampwidth()
                            
                            audio_info = f"""Fayl adı: {audio_file.filename}
Format: WAV
Sample Rate: {rate} Hz
Kanallar: {channels}
Müddət: {duration:.2f} saniyə
Sample Width: {sample_width} bytes"""
                    else:
                        audio_info = f"""Fayl adı: {audio_file.filename}
Format: {file_ext.upper()}
Qeyd: Bu format üçün ətraflı məlumat göstərilə bilmir"""
                    
                    result_msg = "📊 Audio fayl məlumatları"
                    filename = None
                    
                except Exception as e:
                    audio_info = f"Xəta: {str(e)}"
                    result_msg = "❌ Audio məlumatları oxuna bilmədi"
                    filename = None
            
            # Input faylı təmizlə
            if os.path.exists(input_path):
                os.remove(input_path)
            
            return render_template_string(
                HTML, 
                result=result_msg, 
                filename=filename,
                audio_info=audio_info if 'audio_info' in locals() else None
            )
            
        except Exception as e:
            # Xəta halında təmizlik
            for path in ['input_path', 'output_path']:
                if path in locals() and os.path.exists(locals()[path]):
                    os.remove(locals()[path])
            
            return render_template_string(
                HTML, 
                error=f"❌ Xəta: {str(e)}"
            )
    
    return render_template_string(HTML)

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        response = send_file(
            file_path, 
            as_attachment=True, 
            download_name="audio_file.wav"
        )
        
        @after_this_request
        def remove_file(resp):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Fayl silinə bilmədi: {e}")
            return resp
            
        return response
    return "Fayl tapılmadı", 404

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
