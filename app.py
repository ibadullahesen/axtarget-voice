import os
from flask import Flask, request, send_file, render_template_string
from TTS.api import TTS
import uuid
import time

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Modeli əvvəlcədən yükləyirik (build zamanı olur)
print("XTTS modeli endirilir... (ilk dəfə 2-3 dəqiqə çəkəcək)")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False, progress_bar=True)
print("Model hazır! Səs klonlama işləyir")

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Səs Klonlama | AxtarGet Voice</title>
    <meta charset="utf-8">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gradient-to-br from-indigo-900 to-purple-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/10 backdrop-blur-lg rounded-3xl p-10 max-w-4xl w-full shadow-2xl">
        <h1 class="text-5xl font-black text-center text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-pink-400 mb-6">
            Səs Klonlama
        </h1>
        <p class="text-gray-300 text-center text-xl mb-8">5-10 saniyə öz səsinlə danış → istənilən mətni o səslə danışdır!</p>
        
        <form method="post" enctype="multipart/form-data" class="space-y-8">
            <div class="grid md:grid-cols-2 gap-8">
                <div>
                    <label class="block text-cyan-300 font-bold mb-3 text-lg">1. Öz səsini yaz (5-10 saniyə)</label>
                    <input type="file" name="voice" accept="audio/*" required class="block w-full text-cyan-300 file:mr-4 file:py-4 file:px-6 file:rounded-full file:border-0 file:bg-gradient-to-r file:from-cyan-600 file:to-purple-600 file:text-white font-bold">
                </div>
                <div>
                    <label class="block text-pink-300 font-bold mb-3 text-lg">2. Səsləndiriləcək mətn</label>
                    <textarea name="text" rows="5" required placeholder="Salam, mən İbadullahəm. Bu gün Bakıda hava gözəldir..." class="w-full px-6 py-4 rounded-2xl bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400"></textarea>
                </div>
            </div>
            <button type="submit" class="w-full py-6 bg-gradient-to-r from-cyan-500 to-pink-600 text-white text-3xl font-black rounded-2xl hover:scale-105 transition">
                SƏSLƏNDİR
            </button>
        </form>
        
        {% if result %}
        <div class="mt-10 p-8 bg-green-500/20 border-2 border-green-400 rounded-3xl text-center">
            <p class="text-green-300 text-2xl font-bold mb-6">{{ result }}</p>
            <audio controls class="w-full">
                <source src="{{ url_for('download', filename=filename) }}" type="audio/wav">
            </audio>
            <br><br>
            <a href="{{ url_for('download', filename=filename) }}" class="inline-block px-8 py-4 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700">
                AUDIO ENDİR (.wav)
            </a>
        </div>
        {% endif %}
        
        <p class="text-center text-gray-500 mt-12 text-sm">© 2025 AxtarGet Voice – Azərbaycanın ən güclü səs klonlayıcısı</p>
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
            
            os.remove(voice_path)  # səsi sil
            
            filename = os.path.basename(output_path)
            return render_template_string(HTML, result="Uğurla klonlandı!", filename=filename)
    
    return render_template_string(HTML)

@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        response = send_file(file_path, as_attachment=True, download_name="klonlanmış_səs.wav")
        # Faylı endirdikdən sonra sil
        @after_this_request
        def remove_file(response):
            try:
                os.remove(file_path)
            except:
                pass
            return response
        return response
    return "Fayl tapılmadı", 404

# RENDER ÜÇÜN 100% İŞLƏYİR
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
