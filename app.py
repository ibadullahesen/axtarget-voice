from flask import Flask, request, send_file, render_template_string, after_this_request
import os
import uuid
import logging
import tempfile

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# LAZY model loading
tts = None

def load_tts_model():
    global tts
    if tts is None:
        try:
            from TTS.api import TTS
            print("🎵 XTTS v2 modeli yüklənir...")
            tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False, progress_bar=False)
            print("✅ Model hazır!")
        except Exception as e:
            print(f"❌ Model yüklənmədi: {e}")
            raise e

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>AxtarGet Voice – Səs Klonlama</title>
    <meta charset="utf-8">
    <script src="https://cdn.tailwindcss.com"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body class="bg-gradient-to-br from-indigo-900 to-purple-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-6 md:p-10 max-w-4xl w-full shadow-2xl border border-white/20">
        <h1 class="text-4xl md:text-6xl font-black text-center bg-gradient-to-r from-cyan-400 to-pink-500 bg-clip-text text-transparent mb-4">
            AxtarGet Voice
        </h1>
        <p class="text-lg md:text-2xl text-gray-200 text-center mb-6">5-15 saniyə öz səsinlə danış → istənilən mətni o səslə danışdır!</p>

        <form method="post" enctype="multipart/form-data" class="space-y-6" id="voiceForm">
            <div class="grid md:grid-cols-2 gap-6">
                <!-- Səs faylı -->
                <div class="space-y-4">
                    <label class="block text-cyan-300 font-bold text-lg">1. Öz səsini yüklə</label>
                    <div class="border-2 border-dashed border-cyan-400 rounded-2xl p-6 text-center hover:border-cyan-300 transition">
                        <input type="file" name="voice" accept="audio/*" required class="hidden" id="voiceInput">
                        <label for="voiceInput" class="cursor-pointer block">
                            <div class="text-4xl mb-3">🎤</div>
                            <p class="text-cyan-300 font-bold" id="voiceText">Səs faylı seç</p>
                            <p class="text-gray-400 text-sm mt-2">WAV, MP3, OGG (max 10MB)</p>
                        </label>
                    </div>
                    <div id="voiceInfo" class="hidden p-3 bg-cyan-500/20 rounded-xl">
                        <p class="text-cyan-300 text-sm font-bold">Seçilmiş fayl:</p>
                        <p id="voiceName" class="text-white text-xs"></p>
                    </div>
                </div>

                <!-- Mətn -->
                <div class="space-y-4">
                    <label class="block text-pink-300 font-bold text-lg">2. Səsləndiriləcək mətn</label>
                    <textarea name="text" rows="6" required placeholder="Mən İbadullahəm. Bu, mənim klonlanmış səsimdir! Səs texnologiyaları inanılmazdır..." class="w-full px-4 py-3 rounded-2xl bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400 resize-none"></textarea>
                </div>
            </div>

            <!-- Tərcümə seçimi -->
            <div class="bg-white/5 rounded-2xl p-4">
                <label class="block text-green-300 font-bold text-lg mb-2">3. Dil seçimi</label>
                <select name="language" class="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/20 text-white focus:outline-none focus:border-cyan-400">
                    <option value="az">Azərbaycan 🇦🇿</option>
                    <option value="tr">Türk 🇹🇷</option>
                    <option value="en">İngilis 🇺🇸</option>
                    <option value="ru">Rus 🇷🇺</option>
                </select>
            </div>

            <button type="submit" class="w-full py-4 bg-gradient-to-r from-cyan-500 to-pink-600 text-white text-xl font-black rounded-2xl hover:scale-105 transition duration-300 shadow-xl disabled:opacity-50" id="submitBtn">
                🎵 SƏSİ KLONLA
            </button>
        </form>

        <!-- Nəticə -->
        <div id="resultContainer"></div>

        <!-- Statistikalar -->
        <div class="mt-8 grid grid-cols-3 gap-4 text-center">
            <div class="bg-white/5 rounded-xl p-3">
                <div class="text-2xl">🎯</div>
                <p class="text-cyan-300 text-sm">Yüksək Keyfiyyət</p>
            </div>
            <div class="bg-white/5 rounded-xl p-3">
                <div class="text-2xl">⚡</div>
                <p class="text-pink-300 text-sm">Sürətli</p>
            </div>
            <div class="bg-white/5 rounded-xl p-3">
                <div class="text-2xl">🔒</div>
                <p class="text-green-300 text-sm">Təhlükəsiz</p>
            </div>
        </div>

        <p class="text-center text-gray-500 mt-8 text-sm">© 2025 AxtarGet Voice – AI Səs Texnologiyaları</p>
    </div>

    <script>
        const voiceInput = document.getElementById('voiceInput');
        const voiceText = document.getElementById('voiceText');
        const voiceInfo = document.getElementById('voiceInfo');
        const voiceName = document.getElementById('voiceName');
        const submitBtn = document.getElementById('submitBtn');
        const resultContainer = document.getElementById('resultContainer');
        const form = document.getElementById('voiceForm');

        voiceInput.addEventListener('change', function(e) {
            if (this.files[0]) {
                const file = this.files[0];
                if (file.size > 10 * 1024 * 1024) {
                    alert('Fayl çox böyükdür! Maksimum 10MB.');
                    this.value = '';
                    return;
                }
                voiceName.textContent = file.name;
                voiceInfo.classList.remove('hidden');
                voiceText.textContent = 'Fayl seçildi';
            }
        });

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            submitBtn.disabled = true;
            submitBtn.textContent = 'Klonlanır...';

            try {
                const response = await fetch('/clone', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    resultContainer.innerHTML = `
                        <div class="mt-6 p-6 bg-green-600/30 border-2 border-green-400 rounded-2xl text-center">
                            <p class="text-green-300 text-xl font-bold mb-4">${result.message}</p>
                            <audio controls class="w-full mb-4">
                                <source src="${result.download_url}" type="audio/wav">
                            </audio>
                            <a href="${result.download_url}" class="inline-block px-6 py-3 bg-green-600 text-white font-bold rounded-xl hover:bg-green-700 transition">
                                📥 AUDIO ENDİR
                            </a>
                        </div>
                    `;
                } else {
                    resultContainer.innerHTML = `
                        <div class="mt-6 p-4 bg-red-600/30 border-2 border-red-400 rounded-2xl text-center">
                            <p class="text-red-300 font-bold">${result.error}</p>
                        </div>
                    `;
                }
            } catch (error) {
                resultContainer.innerHTML = `
                    <div class="mt-6 p-4 bg-red-600/30 border-2 border-red-400 rounded-2xl text-center">
                        <p class="text-red-300 font-bold">Şəbəkə xətası: ${error.message}</p>
                    </div>
                `;
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '🎵 SƏSİ KLONLA';
            }
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/clone", methods=["POST"])
def clone_voice():
    """Səs klonlama endpoint"""
    try:
        if 'voice' not in request.files:
            return jsonify({'success': False, 'error': '❌ Səs faylı seçilməyib!'})
        
        voice_file = request.files['voice']
        text = request.form.get('text', '').strip()
        language = request.form.get('language', 'az')
        
        if not voice_file or voice_file.filename == '':
            return jsonify({'success': False, 'error': '❌ Səs faylı seçilməyib!'})
        
        if not text:
            return jsonify({'success': False, 'error': '❌ Mətn yazılmayıb!'})
        
        # Modeli yüklə
        load_tts_model()
        
        # Unikal fayl adları
        unique_id = str(uuid.uuid4())
        voice_path = os.path.join(UPLOAD_FOLDER, f"voice_{unique_id}.wav")
        output_path = os.path.join(UPLOAD_FOLDER, f"output_{unique_id}.wav")
        
        # Səs faylını yadda saxla
        voice_file.save(voice_path)
        
        # Səs klonlama
        tts.tts_to_file(
            text=text,
            speaker_wav=voice_path,
            language=language,
            file_path=output_path
        )
        
        # Köhnə faylları təmizlə
        if os.path.exists(voice_path):
            os.remove(voice_path)
        
        return jsonify({
            'success': True,
            'message': '✅ Səs uğurla klonlandı!',
            'download_url': f'/download/{unique_id}.wav'
        })
        
    except Exception as e:
        # Xəta halında təmizlik
        for path in ['voice_path', 'output_path']:
            if path in locals() and os.path.exists(locals()[path]):
                os.remove(locals()[path])
        
        return jsonify({
            'success': False,
            'error': f'❌ Xəta: {str(e)}'
        })

@app.route("/download/<file_id>.wav")
def download(file_id):
    """Audio faylını endir"""
    file_path = os.path.join(UPLOAD_FOLDER, f"output_{file_id}.wav")
    if os.path.exists(file_path):
        response = send_file(
            file_path,
            as_attachment=True,
            download_name="klonlanmis_ses.wav"
        )
        
        @after_this_request
        def remove_file(resp):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
            return resp
            
        return response
    return "Fayl tapılmadı", 404

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "AxtarGet Voice"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
