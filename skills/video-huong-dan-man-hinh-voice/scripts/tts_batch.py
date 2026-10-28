"""Đọc từng cảnh trong scenes.json bằng giọng Bùi Viết Cường -> wav/s<id>.wav
Chạy bằng python của engine:
  VieNeu (nhanh, mặc định): <đường dẫn tới>/VieNeu-TTS/.venv/bin/python tts_batch.py scenes.json wav
  OmniVoice (hay hơn, chậm ~3x): <đường dẫn tới>/OmniVoice/.venv/bin/python tts_batch.py scenes.json wav --engine omni
scenes.json: [{"id":1,"t0":197.9,"t1":215.5,"text":"..."}, ...]   (t0,t1 = đoạn màn hình nguồn, giây)
Dùng giọng khác (VoiceStudio...): bỏ qua file này, tự xuất wav/s<id>.wav theo cùng tên rồi chạy fit_voice.py."""
import json, sys, argparse
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument("scenes"); ap.add_argument("outdir"); ap.add_argument("--engine",default="vieneu")
ap.add_argument("--only",type=int,nargs="*",help="chỉ làm lại các cảnh này"); a=ap.parse_args()
import os
D=Path(os.environ.get("HMT_VOICE_DIR") or (Path(__file__).resolve().parent.parent/"assets"/"giong"))   # mau.wav, mau.txt, omnivoice.prompt; out=Path(a.outdir); out.mkdir(parents=True,exist_ok=True)
sc=[s for s in json.load(open(a.scenes)) if not a.only or s["id"] in a.only]
if a.engine=="omni":
    import torch, soundfile as sf
    from omnivoice import OmniVoice, VoiceClonePrompt
    m=OmniVoice.from_pretrained("k2-fsa/OmniVoice",device_map="cpu",dtype=torch.float16).to("mps")
    p=VoiceClonePrompt.load(str(D/"omnivoice.prompt"))
    for s in sc: sf.write(out/f"s{s['id']}.wav",m.generate(text=s["text"],voice_clone_prompt=p)[0].squeeze(),24000); print(s["id"],flush=True)
else:
    from vieneu import Vieneu
    v=Vieneu(); ref=(D/"mau.txt").read_text(encoding="utf-8").strip()
    for s in sc: v.save(v.infer(text=s["text"],ref_audio=str(D/"mau.wav"),ref_text=ref),str(out/f"s{s['id']}.wav")); print(s["id"],flush=True)
