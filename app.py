from flask import Flask, request, send_file, render_template_string, after_this_request, jsonify
import os
import uuid
import logging

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LAZY model loading
tts_model = None

def load_tts():
    global tts_model
    if tts_model is None:
        try:
            from TTS.api import TTS
            logger.info("🎵 XTTS modeli yüklənir...")
            # TTS 0.20.6 üçün düzgün model adı
            tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
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
<body class="bg-gradient-to-br from-purple-900 to-blue-900 min-h-screen flex items-center justify-center p-4">
    <div class="bg-white/10 backdrop-blur-lg rounded-2xl p-6 max-w-md w-full shadow-xl border border-white/20">
        <h1 class="text-3xl font-black text-center bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent mb-4">
            Səs Klonlama
        </h1>
        
        <form method="post" enctype="multipart/form-data" class="space-y-4" id="voiceForm">
            <div>
                <label class="block text-green-300 font-bold mb-2">Səs faylı</label>
                <input type="file" name="voice" accept="audio/*" required 
                       class="w-full text-white text-sm file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-green-600 file:text-white">
            </div>
            
            <div>
                <label class="block text-blue-300 font-bold mb-2">Mətn</label>
                <textarea name="text" rows="3" required placeholder="Mənim səsimlə oxu..." 
                          class="w-full px-3 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 text-sm"></textarea>
            </div>
            
            <button type="submit" class="w-full py-3 bg-gradient-to-r from-green-500 to-blue-600 text-white font-bold rounded-lg hover:scale-105 transition">
                🎵 Klonla
            </button>
        </form>

        <div id="result" class="mt-4"></div>
    </div>

    <script>
        document.getElementById('voiceForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const button = this.querySelector('button');
            button.disabled = true;
            button.textContent = 'İşlənir...';

            try {
                const response = await fetch('/clone', {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('result').innerHTML = `
                        <div class="p-4 bg-green-600/20 border border-green-400 rounded-lg text-center">
                            <p class="text-green-300 font-bold mb-2">${result.message}</p>
                            <audio controls class="w-full mb-2">
                                <source src="${result.download_url}" type="audio/wav">
                            </audio>
                            <a href="${result.download_url}" class="text-blue-300 text-sm underline">Endir</a>
                        </div>
                    `;
                } else {
                    document.getElementById('result').innerHTML = `
                        <div class="p-3 bg-red-600/20 border border-red-400 rounded-lg">
                            <p class="text-red-300 text-sm">${result.error}</p>
                        </div>
                    `;
                }
            } catch (error) {
                document.getElementById('result').innerHTML = `
                    <div class="p-3 bg-red-600/20 border border-red-400 rounded-lg">
                        <p class="text-red-300 text-sm">Xəta baş verdi</p>
                    </div>
                `;
            } finally {
                button.disabled = false;
                button.textContent = '🎵 Klonla';
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
    try:
        if 'voice' not in request.files:
            return jsonify({'success': False, 'error': 'Səs faylı seçilməyib!'})
        
        voice_file = request.files['voice']
        text = request.form.get('text', '').strip()
        
        if not voice_file or voice_file.filename == '':
            return jsonify({'success': False, 'error': 'Səs faylı seçilməyib!'})
        
        if not text:
            return jsonify({'success': False, 'error': 'Mətn yazılmayıb!'})
        
        load_tts()
        
        unique_id = str(uuid.uuid4())
        voice_path = os.path.join(UPLOAD_FOLDER, f"voice_{unique_id}.wav")
        output_path = os.path.join(UPLOAD_FOLDER, f"output_{unique_id}.wav")
        
        voice_file.save(voice_path)
        
        tts_model.tts_to_file(
            text=text,
            speaker_wav=voice_path,
            language="az",
            file_path=output_path
        )
        
        if os.path.exists(voice_path):
            os.remove(voice_path)
        
        return jsonify({
            'success': True,
            'message': 'Səs klonlandı!',
            'download_url': f'/download/{unique_id}'
        })
        
    except Exception as e:
        logger.error(f"Xəta: {e}")
        return jsonify({
            'success': False,
            'error': f'Xəta: {str(e)}'
        })

@app.route("/download/<file_id>")
def download(file_id):
    file_path = os.path.join(UPLOAD_FOLDER, f"output_{file_id}.wav")
    if os.path.exists(file_path):
        response = send_file(file_path, as_attachment=True, download_name="ses.wav")
        @after_this_request
        def remove_file(resp):
            try:
                os.remove(file_path)
            except:
                pass
            return resp
        return response
    return "Fayl tapılmadı", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
