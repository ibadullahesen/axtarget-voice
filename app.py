import os
import torch
from TTS.api import TTS
import gradio as gr
import time
import warnings
warnings.filterwarnings("ignore")

# Modeli yükləyirik (ilk dəfə bir az çəkəcək, sonra sürətli)
print("XTTS v2 modeli endirilir... (ilk dəfədir)")
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True, gpu=False)
print("Model hazır! Səs klonlama işləyir")

def voice_clone(text, audio_file):
    if not text or not text.strip():
        return None, "Mətn yazın!"
    if not audio_file:
        return None, "Mikrofonla 5-10 saniyə səs yazın!"

    output_file = f"output_{int(time.time())}.wav"
    
    tts.tts_to_file(
        text=text,
        speaker_wav=audio_file,
        language="az",
        file_path=output_file
    )
    
    return output_file, "Uğurla yaradıldı! Aşağıda dinlə və ya endir"

# Gözəl interfeys
with gr.Blocks(title="AxtarGet Voice", theme=gr.themes.Soft()) as demo:
    gr.HTML("""
    <div style="text-align:center; padding:30px; background:linear-gradient(135deg,#667eea,#764ba2); border-radius:20px; color:white;">
        <h1> AxtarGet Voice – Səs Klonlama</h1>
        <p><b>5-10 saniyə öz səsinlə danış → istənilən mətni o səslə danışdır!</b></p>
        <p style="font-size:18px;">Mükəmməl Azərbaycan dili • Bakı, Gəncə, Şəki vurğuları belə tutur</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(label="Səs yaz", source="microphone", type="filepath")
        with gr.Column(scale=2):
            text_input = gr.Textbox(
                label="Səsləndiriləcək mətn",
                placeholder="Salam, mən İbadullahəm. Bu gün Bakıda hava 25 dərəcədir...",
                lines=6
            )
    
    btn = gr.Button("Səsləndir", variant="primary", size="lg")
    
    with gr.Row():
        audio_output = gr.Audio(label="AI səsinlə danışır", type="filepath")
        status = gr.Textbox(label="Status", interactive=False)
    
    btn.click(fn=voice_clone, inputs=[text_input, audio_input], outputs=[audio_output, status])
    
    gr.HTML("""
    <div style="text-align:center; padding:20px; color:#666; margin-top:30px;">
        © 2025 <a href="https://axtarget.xyz" style="color:#764ba2; font-weight:bold;">AxtarGet</a> 
        – Azərbaycanın ən güclü pulsuz AI səs klonlayıcısı<br>
        <small>Render Free-də işləyir • Gündə 300+ istifadə</small>
    </div>
    """)

# RENDER ÜÇÜN MÜTLƏQ BELƏ OLMALIDIR!!!
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        quiet=True
    )
