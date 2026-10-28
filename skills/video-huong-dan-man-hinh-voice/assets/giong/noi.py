"""Đọc văn bản bằng giọng Bùi Viết Cường.
  ../OmniVoice-test/.venv/bin/python noi.py omni   "Văn bản" ra.wav
  ../Voice_VieNeu-TTS/.venv/bin/python noi.py vieneu "Văn bản" ra.wav
"""
import sys
from pathlib import Path
D = Path(__file__).parent
engine, text, out = sys.argv[1:4]
if engine == "omni":
    import torch, soundfile as sf
    from omnivoice import OmniVoice, VoiceClonePrompt
    m = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map="cpu", dtype=torch.float16).to("mps")
    a = m.generate(text=text, voice_clone_prompt=VoiceClonePrompt.load(str(D/"omnivoice.prompt")))
    sf.write(out, a[0].squeeze(), 24000)
else:
    from vieneu import Vieneu
    v = Vieneu()
    v.save(v.infer(text=text, ref_audio=str(D/"mau.wav"), ref_text=(D/"mau.txt").read_text(encoding="utf-8").strip()), out)
print("ok", out)
