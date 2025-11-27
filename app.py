from flask import Flask, request, send_file, render_template_string, after_this_request
from TTS.api import TTS
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Modeli yükləyirik (ilk dəfə 3-5 dəqiqə çəkəcək)
print("XTTS v2 modeli endirilir... (ilk dəfədir, gözlə)")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False, progress_bar=True)
print("Model hazır! Səs klonlama aktivdir")

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AxtarGet Voice – Səs Klonlama</title>
    <meta charset="utf-8">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-purple-900 to-black min-h-screen flex items-center justify-center p-6">
    <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-12 max-w-4xl w-full shadow-2xl border border-white/20">
        <h1 class="text-6xl font-black text-center bg-gradient-to-r from-cyan-400 to-pink-500 bg-clip-text text-transparent mb-6">
            Səs Klonlama
        </h1>
        <p class="text-xl text-gray-300 text-center mb-10">5-15 saniyə öz səsinlə danış → istənilən mətni o səslə danışdır!</p>

        <form method="post" enctype="multipart/form-data" class="space-y-8">
            <div class="grid md:grid-cols-2 gap-8">
                <div>
                    <label class="block text-cyan-300 font-bold text-lg mb-3">1. Öz səsini yüklə (wav/mp3)</label>
                    <input type="file" name="voice" accept="audio/*" required class="block w-full text-white file:mr-4 file:py-4 file:px-8 file:rounded-full file:border-0 file:bg-gradient-to-r file:from-cyan-600 file:to-purple-600 file:text-white file:font-bold">
                </div>
                <div>
                    <label class="block text-pink-300 font-bold text-lg mb-3">2. Səsləndiriləcək mətn</label>
                    <textarea name="text" rows="6" required placeholder="Salam qardaş, bu gün hava necədir Bakıda?" class="w-full px-6 py-4 rounded-2xl bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400"></textarea>
                </div>
            </div>
            <button type="submit" class="w-full py-6 bg-gradient-to-r from-cyan-500 to-pink-600 text-white text-3xl font-black rounded-2xl hover:scale-105 transition duration-300">
                SƏSLƏNDİR
            </button>
        </form>

        {% if result %}
        <div class="mt-12 p-8 bg-green-600/30 border-2 border-green-400 rounded-3xl text-center">
            <p class="text-2xl text-green-300 font-bold mb-6">{{ result }}</p>
            <audio controls class="w-full mb-6">
                <source src="{{ url_for('download', filename=filename) }}" type="audio/wav">
            </audio>
            <br>
            <a href="{{ url_for('download', filename=filename) }}" class="inline-block px-10 py-5 bg-green-600 text-white text-xl font-bold rounded-xl hover:bg-green-700">
                AUDIO ENDİR (.wav)
            </a>
        </div>
        {% endif %}

        <p class="text-center text-gray-500 mt-16 text-sm">© 2025 AxtarGet Voice – Azərbaycanın ən güclü səs klonlayıcısı</p>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        voice_file = request.files["voice"]
        text = request.form["text"].strip()
        
        if voice_file and text:
            voice_path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".wav")
            output_path = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + ".wav")
            
            voice_file.save(voice_path)
            
            tts.tts_to_file(text=text, speaker_wav=voice_path, language="az", file_path=output_path)
            
            os.remove(voice_path)
            
            filename = os.path.basename(output_path)
            return render_template_string(HTML, result="Səs uğurla klonlandı!", filename=filename)
    
    return render_template_string(HTML)

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        response = send_file(file_path, as_attachment=True, download_name="klonlanmis_ses.wav")
        @after_this_request
        def remove_file(resp):
            try:
                os.remove(file_path)
            except:
                pass
            return resp
        return response
    return "Fayl tapılmayıb", 404

# RENDER ÜÇÜN HEÇ NƏ YAZMA – Procfile ilə işləyəcək
