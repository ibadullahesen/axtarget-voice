import os
import torch
from TTS.api import TTS
import gradio as gr
import time

# XTTS-v2 modelini yükləyirik (Azərbaycan dilini mükəmməl bilir)
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False, progress_bar=True)

def voice_clone_and_speak(reference_audio, text, language="az"):
    if not text.strip():
        return None, "Mətn yazın!"
    
    output_path = f"output_{int(time.time())}.wav"
    tts.tts_to_file(text=text,
                    speaker_wav=reference_audio,
                    language=language,
                    file_path=output_path)
    return output_path, "Uğurla yaradıldı!"

# Gradio interfeysi
iface = gr.Interface(
    fn=voice_clone_and_speak,
    inputs=[
        gr.Audio(source="microphone", type="filepath", label="5-10 saniyə öz səsinlə danış"),
        gr.Textbox(label="Səsləndiriləcək mətn", placeholder="Salam, mən İbadullahəm...", lines=4),
    ],
    outputs=[
        gr.Audio(label="AI səsinlə danışır"),
        gr.Textbox(label="Status")
    ],
    title="🗣 AxtarGet Voice – Səs Klonlama",
    description="5-10 saniyə səs yaz → istənilən mətni öz səsinlə danışdır!",
    theme=gr.themes.Soft(),
    allow_flagging="never"
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)
