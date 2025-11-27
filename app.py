from flask import Flask, request, send_file, render_template_string, after_this_request, jsonify
import os
import uuid
import logging

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LAZY model loading
tts_model = None

def load_tts():
    global tts_model
    if tts_model is None:
        try:
            from TTS.api import TTS
            logger.info("🎵 XTTS v2 modeli yüklənir...")
            tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False, progress_bar=False)
            logger.info("✅ Model hazır!")
        except Exception as e:
            logger.error(f"❌ Model yüklənmədi: {e}")
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
    <div class="bg-white/10 backdrop-blur-xl rounded-3xl p-6 md:p-8 max-w-2xl w-full shadow-2xl border border-white/20">
        <h1 class="text-3xl md:text-4xl font-black text-center bg-gradient-to-r from-cyan-400 to-pink-500 bg-clip-text text-transparent mb-4">
            AxtarGet Voice
        </h1>
        <p class="text-gray-200 text-center mb-6">Səsini yüklə, mətni yaz - eyni səslə oxusun!</p>

        <form method="post" enctype="multipart/form-data" class="space-y-6" id="voiceForm">
            <!-- Səs faylı -->
            <div>
                <label class="block text-cyan-300 font-bold mb-2">1. Səs faylı yüklə</label>
                <div class="border-2 border-dashed border-cyan-400 rounded-xl p-4 text-center hover:border-cyan-300 transition">
                    <input type="file" name="voice" accept="audio/*" required class="hidden" id="voiceInput">
                    <label for="voiceInput" class="cursor-pointer block">
                        <div class="text-2xl mb-2">🎤</div>
                        <p class="text-cyan-300 font-bold text-sm" id="voiceText">Səs faylı seç</p>
                        <p class="text-gray-400 text-xs mt-1">WAV, MP3 (max 10MB)</p>
                    </label>
                </div>
                <div id="voiceInfo" class="hidden mt-2 p-2 bg-cyan-500/20 rounded-lg">
                    <p class="text-cyan-300 text-xs font-bold">Seçildi: <span id="voiceName" class="text-white"></span></p>
                </div>
            </div>

            <!-- Mətn -->
            <div>
                <label class="block text-pink-300 font-bold mb-2">2. Səsləndiriləcək mətn</label>
                <textarea name="text" rows="4" required placeholder="Mənim səsimlə bu mətni oxu..." class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:border-cyan-400 text-sm resize-none"></textarea>
            </div>

            <!-- Dil seçimi -->
            <div>
                <label class="block text-green-300 font-bold mb-2">3. Dil</label>
                <select name="language" class="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/20 text-white focus:outline-none focus:border-cyan-400 text-sm">
                    <option value="az">Azərbaycan 🇦🇿</option>
                    <option value="tr">Türk 🇹🇷</option>
                    <option value="en">İngilis 🇺🇸</option>
                </select>
            </div>

            <button type="submit" class="w-full py-3 bg-gradient-to-r from-cyan-500 to-pink-600 text-white font-bold rounded-xl hover:scale-105 transition duration-300 shadow-lg disabled:opacity-50" id="submitBtn">
                🎵 SƏSİ KLONLA
            </button>
        </form>

        <div id="resultContainer" class="mt-6"></div>

        <div class="mt-6 text-center">
            <button onclick="resetForm()" class="px-4 py-2 bg-gray-600 text-white text-sm rounded-lg hover:bg-gray-700 transition">
                🔄 Təmizlə
            </button>
        </div>

        <p class="text-center text-gray-500 mt-6 text-xs">© 2025 AxtarGet Voice</p>
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

        function resetForm() {
            voiceInput.value = '';
            voiceInfo.classList.add('hidden');
            voiceText.textContent = 'Səs faylı seç';
            resultContainer.innerHTML = '';
            form.reset();
        }

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            if (!voiceInput.files[0]) {
                alert('Zəhmət olmasa səs faylı seçin!');
                return;
            }

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
                        <div class="p-4 bg-green-600/30 border border-green-400 rounded-xl text-center">
                            <p class="text-green-300 font-bold mb-3">${result.message}</p>
                            <audio controls class="w-full mb-3">
                                <source src="${result.download_url}" type="audio/wav">
                            </audio>
                            <a href="${result.download_url}" class="inline-block px-4 py-2 bg-green-600 text-white text-sm font-bold rounded-lg hover:bg-green-700 transition">
                                📥 Endir
                            </a>
                        </div>
                    `;
                } else {
                    resultContainer.innerHTML = `
                        <div class="p-4 bg-red-600/30 border border-red-400 rounded-xl text-center">
                            <p class="text-red-300 font-bold">${result.error}</p>
                        </div>
                    `;
                }
            } catch (error) {
                resultContainer.innerHTML = `
                    <div class="p-4 bg-red-600/30 border border-red-400 rounded-xl text-center">
                        <p class="text-red-300 font-bold">Şəbəkə xətası</p>
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
        load_tts()
        
        # Unikal fayl adları
        unique_id = str(uuid.uuid4())
        voice_path = os.path.join(UPLOAD_FOLDER, f"voice_{unique_id}.wav")
        output_path = os.path.join(UPLOAD_FOLDER, f"output_{unique_id}.wav")
        
        # Səs faylını yadda saxla
        voice_file.save(voice_path)
        
        # Səs klonlama
        tts_model.tts_to_file(
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
            'download_url': f'/download/{unique_id}'
        })
        
    except Exception as e:
        logger.error(f"Klonlama xətası: {e}")
        # Xəta halında təmizlik
        for path in ['voice_path', 'output_path']:
            if path in locals() and os.path.exists(locals()[path]):
                try:
                    os.remove(locals()[path])
                except:
                    pass
        
        return jsonify({
            'success': False,
            'error': f'❌ Xəta: {str(e)}'
        })

@app.route("/download/<file_id>")
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
