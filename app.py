import os
import torch
from TTS.api import TTS
import gradio as gr
import time
import warnings
warnings.filterwarnings("ignore")

# Modeli ilk dəfə yükləyirik (build zamanı olur)
print("XTTS v2 modeli endirilir... (ilk dəfədir, biraz gözlə)")
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True, gpu=False)
print("Model hazır! Artıq istifadə edə bilərsən")

def voice_clone(text, audio_file):
    if not text or not text.strip():
        return None, "Mətn yazın!"
    if not audio_file:
        return None, "Səs yazın (mikrofonla 5-10 saniyə)"

    output_file = f"output_{int(time.time())}.wav"
    
    tts.tts_to_file(
        text=text,
        speaker_wav=audio_file,
        language="az",
        file_path=output_file
    )
    
    return output_file, "Uğurla yaradıldı! Aşağıda dinlə və ya endir"

# Gözəl Gradio interfeysi
with gr.Blocks(title="AxtarGet Voice", theme=gr.themes.Soft()) as demo:
    gr.HTML("""
    <div style="text-align:center; padding:20px;">
        <h1>AxtarGet Voice – Səs Klonlama</h1>
        <p><b>5-10 saniyə öz səsinlə danış → istənilən mətni o səslə danışdır!</b></p>
        <p style="color:#10b981; font-weight:bold;">Mükəmməl Azərbaycan dili (Bakı, Gəncə, Şəki vurğuları belə tutur)</p>
    </div>
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            audio_input = gr.Audio(
                label="Səs yaz (mikrofonla)",
                source="microphone",
                type="filepath"
            )
        with gr.Column(scale=2):
            text_input = gr.Textbox(
                label="Səsləndiriləcək mətn",
                placeholder="Salam, mən İbadullahəm. Bu gün hava çox gözəldir...",
                lines=5
            )
    
    generate_btn = gr.Button("Səsləndir", variant="primary", size="lg")
    
    with gr.Row():
        audio_output = gr.Audio(label="AI səsinlə danışır", type="filepath")
        status = gr.Textbox(label="Status", interactive=False)
    
    # SƏHV BURADA İDİ – düzəldildi!
    generate_btn.click(
        fn=voice_clone,
        inputs=[text_input, audio_input],
        outputs=[audio_output, status]
    )
    
    gr.HTML("""
    <div style="text-align:center; padding:20px; color:#666;">
        © 2025 <a href="https://axtarget.xyz" style="color:#10b981;">AxtarGet</a> – Azərbaycanın ən güclü AI səs klonlayıcısı<br>
        <small>Render Free-də pulsuz işləyir • Gündə 300+ istifadə</small>
    </div>
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, quiet=True)
